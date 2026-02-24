# Eduflow RAG Agent Workflow Documentation

This document explains the end-to-end workflow of the Retrieval-Augmented Generation (RAG) agent in the `ai-service`. It covers how video lessons are processed into searchable vectors (Ingestion) and how student questions are answered using those vectors (Query/Generation).

## 1. Ingestion Pipeline (Video to Vectors)

The ingestion pipeline is an asynchronous process triggered when a new video lesson is uploaded. It is handled by Celery background workers.

### Component Flow (`app/tasks.py` -> `process_video_task`)
1. **Trigger & Status Initialization**: 
   - A video upload triggers the `process_video_task`. 
   - The status for the `lesson_id` is updated to `"processing"` in the `ProcessingStatus` table via `VectorService`.
2. **Download & Transcription (`TranscriptionService`)**: 
   - The video is downloaded from its S3 URL.
   - It is passed through a Whisper model to generate a text transcript broken down by timestamped segments.
3. **Chunking (`ChunkingService`)**: 
   - The timestamped transcript segments are stitched and split into optimally sized chunks.
4. **Embedding Generation (`EmbeddingService`)**: 
   - The text chunks are converted into vector embeddings. 
   - *Note: Uses Hugging Face models if an API key is available, falling back to OpenAI embeddings.*
5. **Vector Storage (`VectorService`)**: 
   - The chunks and their corresponding embeddings are saved to the PostgreSQL database using the `pgvector` extension. 
   - The data is stored in the `lesson_embeddings` table (`LessonEmbedding` model) with metadata like `tenant_id`, `course_id`, `lesson_id`, `start_time`, and `end_time`.
6. **Completion**: 
   - The `ProcessingStatus` is marked as `"completed"` with the `chunks_count`.

---

## 2. Query Pipeline (Student Q&A)

When a student asks a doubt about a lesson, the system attempts to answer it using the transcript context.

### Endpoint Flow (`POST /api/v1/rag/ask`)
1. **Request Reception**: 
   - The frontend sends a `RAGRequest` containing `course_id`, `lesson_id`, `question`, and optionally the student's `current_time` in the video.
2. **Readiness Check**: 
   - `VectorService.has_embeddings()` checks if vector data exists for the given lesson.
   - *If Processing*: Returns a `202 Accepted` indicating the lesson is still being processed.
   - *If Missing*: Falls back to a direct LLM query (`RAGService.fallback_ask()`) that explicitly states the transcript is unavailable.
3. **RAG Orchestration (`RAGService.ask()`)**:
   - **Question Embedding**: The student's question is embedded into a vector.
   - **Similarity Search (`VectorService.similarity_search`)**: Uses `pgvector`'s cosine distance operator (`<=>`) to find the most semantically relevant transcript chunks.
   - **Time-Proximity Boost**: If `current_time` is provided, a relevancy boost (up to +0.1) is applied to chunks that occur within 120 seconds of the student's current video position. This ensures answers are highly relevant to what they are currently watching.
   - **Context Building**: The top `K` most relevant chunks are concatenated into a formatted transcript context string.
   - **LLM Generation (`RAGService._call_llm()`)**: The chosen LLM (Mistral-7B via Hugging Face or GPT-4o-mini via OpenAI) is prompted with the context and strict instructions to answer *only* based on the provided transcript.
4. **Response Delivery**: 
   - The generated answer and the source references (start/end times and text previews) are returned to the user in a `RAGResponse`.

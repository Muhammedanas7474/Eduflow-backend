"""
RAG (Retrieval-Augmented Generation) service.
Orchestrates: embed question → similarity search → build prompt → LLM answer.
"""

import logging

from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from openai import OpenAI

logger = logging.getLogger(__name__)

# Lazy-loaded OpenAI client
_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if settings.huggingface_api_key:
            _client = OpenAI(
                base_url="https://router.huggingface.co/v1/",
                api_key=settings.huggingface_api_key,
            )
        else:
            _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def _get_model_name() -> str:
    return (
        "mistralai/Mistral-7B-Instruct-v0.2"
        if settings.huggingface_api_key
        else "gpt-4o-mini"
    )


SYSTEM_PROMPT = """You are an AI course assistant for an online learning platform.

Your role is to answer student questions ONLY using the transcript context provided below.

Rules:
1. Answer ONLY based on the transcript. Do not use outside knowledge.
2. If the answer is not found in the transcript, say: "This topic was not covered in the lesson."
3. Be concise and clear. Use bullet points when listing multiple things.
4. When referencing specific parts of the lesson, mention the approximate timestamp.
5. If the student asks something unrelated to the lesson content, politely redirect them.

Transcript Context:
---
{context}
---
"""


class RAGService:
    """Orchestrate the full RAG query flow."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()

    def ask(
        self,
        lesson_id: int,
        question: str,
        current_time: float | None = None,
        top_k: int = 5,
    ) -> dict:
        """
        Answer a student question using RAG.

        Args:
            lesson_id: The lesson to search
            question: Student's question
            current_time: Student's current video position (seconds)
            top_k: Number of relevant chunks to retrieve

        Returns:
            {answer, sources: [{start, end, text_preview}]}
        """
        # Step 1: Embed the question
        logger.info(f"RAG query: lesson={lesson_id}, q='{question[:80]}...'")
        question_embedding = self.embedding_service.embed_text(question)

        # Step 2: Similarity search with optional time boost
        relevant_chunks = self.vector_service.similarity_search(
            lesson_id=lesson_id,
            query_embedding=question_embedding,
            top_k=top_k,
            current_time=current_time,
        )

        if not relevant_chunks:
            return {
                "answer": "No transcript data is available for this lesson yet. "
                "The lesson may still be processing.",
                "sources": [],
            }

        # Step 3: Build context from retrieved chunks
        context = self._build_context(relevant_chunks)

        # Step 4: Call LLM
        answer = self._call_llm(context, question)

        # Step 5: Build response with sources
        sources = [
            {
                "start": chunk["start_time"],
                "end": chunk["end_time"],
                "text_preview": (
                    chunk["text"][:100] + "..."
                    if len(chunk["text"]) > 100
                    else chunk["text"]
                ),
            }
            for chunk in relevant_chunks
        ]

        logger.info(f"RAG answer generated: {len(sources)} sources")
        return {
            "answer": answer,
            "sources": sources,
        }

    def _build_context(self, chunks: list[dict]) -> str:
        """Build the context string from retrieved chunks."""
        parts = []
        for i, chunk in enumerate(chunks, 1):
            start_min = int(chunk["start_time"] // 60)
            start_sec = int(chunk["start_time"] % 60)
            end_min = int(chunk["end_time"] // 60)
            end_sec = int(chunk["end_time"] % 60)

            parts.append(
                f"[Segment {i} | {start_min}:{start_sec:02d} - "
                f"{end_min}:{end_sec:02d}]\n{chunk['text']}"
            )

        return "\n\n".join(parts)

    def _call_llm(self, context: str, question: str) -> str:
        """Call GPT-4o-mini with the context and question."""
        client = _get_client()

        try:
            response = client.chat.completions.create(
                model=_get_model_name(),
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT.format(context=context),
                    },
                    {
                        "role": "user",
                        "content": question,
                    },
                ],
                temperature=0.3,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return (
                "I'm sorry, I couldn't generate an answer right now. "
                "Please try again later."
            )

    def fallback_ask(self, question: str) -> dict:
        """
        Fallback: answer a question using OpenAI directly (no RAG context).
        Used when lesson embeddings are not available.
        """
        client = _get_client()

        fallback_prompt = (
            "You are an AI course assistant for an online learning platform. "
            "The lesson transcript is not available, so you cannot verify if the topic is covered. "
            "You must decline to answer any specific subject-matter questions to prevent hallucination. "
            "Reply strictly with: 'I can only answer questions based on the lesson transcript, which is not currently available for this lesson.'"
        )

        try:
            response = client.chat.completions.create(
                model=_get_model_name(),
                messages=[
                    {"role": "system", "content": fallback_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0.4,
                max_tokens=1000,
            )
            answer = response.choices[0].message.content
            logger.info("Fallback (no RAG) answer generated")
            return {
                "answer": answer,
                "sources": [],
            }
        except Exception as e:
            logger.error(f"Fallback LLM call failed: {e}")
            return {
                "answer": "I'm sorry, I couldn't generate an answer right now. Please try again later.",
                "sources": [],
            }

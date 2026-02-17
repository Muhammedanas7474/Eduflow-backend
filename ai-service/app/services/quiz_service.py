import json
import logging
import random
import re
import textwrap

import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download

    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-load the Flan-T5 model so startup stays fast when not generating quizzes
# ---------------------------------------------------------------------------
_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        logger.info("Loading Flan-T5-base model … (first call only)")
        from transformers import pipeline as hf_pipeline

        _pipeline = hf_pipeline(
            "text2text-generation",
            model="google/flan-t5-base",
            device=-1,  # CPU
        )
        logger.info("Flan-T5-base model loaded successfully.")
    return _pipeline


class QuizService:

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @staticmethod
    def generate_quiz(text: str, num_questions: int = 5) -> dict:
        """
        Generate conceptual MCQs from the given text using Flan-T5.
        Uses multi-section chunking for better coverage.
        Falls back to spaCy-based generation if Flan-T5 fails.
        """
        # Split text into meaningful chunks for diverse questions
        chunks = QuizService._split_into_chunks(text, max_chars=2500)

        try:
            questions = QuizService._generate_with_flan_t5(chunks, num_questions)
            if questions and len(questions) >= 1:
                return {"questions": questions[:num_questions]}
        except Exception as e:
            logger.warning(f"Flan-T5 generation failed, falling back to spaCy: {e}")

        # Fallback: spaCy-based extraction
        questions = QuizService._generate_with_spacy(text, num_questions)
        return {"questions": questions}

    # ------------------------------------------------------------------
    # Text chunking — extract questions from different sections
    # ------------------------------------------------------------------
    @staticmethod
    def _split_into_chunks(text: str, max_chars: int = 2500) -> list:
        """
        Split text into paragraph-aware chunks so questions cover
        different parts of the document, not just the first few pages.
        """
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para or len(para) < 20:
                continue

            if len(current) + len(para) + 2 > max_chars:
                if current:
                    chunks.append(current.strip())
                current = para
            else:
                current += "\n\n" + para if current else para

        if current.strip():
            chunks.append(current.strip())

        # If text is too short for multiple chunks, just return it as one
        if not chunks:
            chunks = [text[:max_chars]]

        return chunks

    # ------------------------------------------------------------------
    # Flan-T5 generation — multi-section
    # ------------------------------------------------------------------
    @staticmethod
    def _generate_with_flan_t5(chunks: list, num_questions: int) -> list:
        pipe = _get_pipeline()
        all_questions = []

        # Distribute questions across chunks
        questions_per_chunk = max(1, num_questions // len(chunks))
        remainder = num_questions % len(chunks)

        for chunk_idx, chunk in enumerate(chunks):
            if len(all_questions) >= num_questions:
                break

            q_count = questions_per_chunk + (1 if chunk_idx < remainder else 0)

            for i in range(q_count):
                if len(all_questions) >= num_questions:
                    break

                # Vary the prompt style for diversity
                prompt = QuizService._build_prompt(chunk, i, len(all_questions))

                result = pipe(
                    prompt,
                    max_new_tokens=300,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                )

                raw = result[0]["generated_text"].strip()
                parsed = QuizService._parse_question_json(raw)
                if parsed:
                    # Deduplicate — skip if question is too similar
                    if not QuizService._is_duplicate(parsed, all_questions):
                        all_questions.append(parsed)

        return all_questions

    @staticmethod
    def _build_prompt(text: str, question_idx: int, total_so_far: int) -> str:
        """Build varied prompts for diverse question generation."""
        prompts = [
            textwrap.dedent(
                f"""\
                Read the following passage carefully and create a multiple-choice question
                that tests deep understanding of the key concepts discussed.
                Avoid simple definition or recall questions.

                Passage:
                {text}

                Create a challenging conceptual question. Return ONLY valid JSON:
                {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ..."}}
            """
            ),
            textwrap.dedent(
                f"""\
                Based on the passage below, create a multiple-choice question that requires
                the reader to apply or analyze the information, not just recall facts.

                Passage:
                {text}

                Generate one MCQ. Return ONLY valid JSON:
                {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ..."}}
            """
            ),
            textwrap.dedent(
                f"""\
                From the following educational content, create a thought-provoking
                multiple-choice question that tests whether the student truly understands
                the relationships and implications of the concepts.

                Content:
                {text}

                Return ONLY valid JSON:
                {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ..."}}
            """
            ),
        ]

        return prompts[(total_so_far + question_idx) % len(prompts)]

    @staticmethod
    def _is_duplicate(new_q: dict, existing: list, threshold: float = 0.6) -> bool:
        """Check if a question is too similar to existing ones."""
        new_text = new_q.get("question", "").lower()
        for eq in existing:
            existing_text = eq.get("question", "").lower()
            # Simple word overlap check
            new_words = set(new_text.split())
            existing_words = set(existing_text.split())
            if not new_words or not existing_words:
                continue
            overlap = len(new_words & existing_words) / max(
                len(new_words), len(existing_words)
            )
            if overlap > threshold:
                return True
        return False

    # ------------------------------------------------------------------
    # JSON parsing helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_question_json(raw: str) -> dict | None:
        """Try to extract a valid question dict from model output."""
        # Try direct JSON parse
        try:
            obj = json.loads(raw)
            if QuizService._validate_question(obj):
                return obj
        except json.JSONDecodeError:
            pass

        # Try to find JSON block inside text
        match = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
        if match:
            try:
                obj = json.loads(match.group())
                if QuizService._validate_question(obj):
                    return obj
            except json.JSONDecodeError:
                pass

        # Build a question from the raw text as last resort
        return QuizService._build_from_raw(raw)

    @staticmethod
    def _validate_question(obj: dict) -> bool:
        return (
            isinstance(obj, dict)
            and "question" in obj
            and "options" in obj
            and "correct_answer" in obj
            and isinstance(obj["options"], list)
            and len(obj["options"]) >= 2
        )

    @staticmethod
    def _build_from_raw(raw: str) -> dict | None:
        """
        Last-resort: if the model returned a plain-text question,
        wrap it into a valid structure.
        """
        if "?" in raw and len(raw) < 500:
            q_text = raw.split("?")[0].strip() + "?"
            return {
                "question": q_text,
                "options": [
                    "A) True",
                    "B) False",
                    "C) Partially true",
                    "D) Cannot be determined",
                ],
                "correct_answer": "A) True",
            }
        return None

    # ------------------------------------------------------------------
    # spaCy fallback
    # ------------------------------------------------------------------
    @staticmethod
    def _generate_with_spacy(text: str, num_questions: int) -> list:
        doc = nlp(text[:50000])  # spaCy can handle more text

        # Extract meaningful noun chunks and sentences
        sentences = [
            sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 30
        ]
        concepts = list(
            set(
                [
                    chunk.text.strip()
                    for chunk in doc.noun_chunks
                    if len(chunk.text.strip()) > 3
                ]
            )
        )

        questions = []
        used_concepts = set()

        for sent in sentences[: num_questions * 2]:
            if len(questions) >= num_questions:
                break

            # Find a concept in this sentence
            sent_doc = nlp(sent)
            sent_concepts = [
                chunk.text.strip()
                for chunk in sent_doc.noun_chunks
                if chunk.text.strip() in concepts
                and chunk.text.strip() not in used_concepts
            ]

            if not sent_concepts:
                continue

            target = sent_concepts[0]
            used_concepts.add(target)

            # Create a fill-in-the-blank style question
            question_text = sent.replace(target, "______")
            if not question_text.endswith("?"):
                question_text = f"What completes this statement? {question_text}"

            # Generate distractors from other concepts
            distractors = [c for c in concepts if c != target]
            random.shuffle(distractors)
            distractors = distractors[:3]

            while len(distractors) < 3:
                distractors.append("None of the above")

            options = [target] + distractors[:3]
            random.shuffle(options)

            # Label with A/B/C/D
            labeled_options = [f"{chr(65 + j)}) {opt}" for j, opt in enumerate(options)]
            correct_label = next(
                lbl for lbl, opt in zip(labeled_options, options) if opt == target
            )

            questions.append(
                {
                    "question": question_text,
                    "options": labeled_options,
                    "correct_answer": correct_label,
                }
            )

        # If we still don't have enough, add concept-based questions
        for concept in concepts:
            if len(questions) >= num_questions:
                break
            if concept in used_concepts:
                continue

            used_concepts.add(concept)

            distractors = [c for c in concepts if c != concept]
            random.shuffle(distractors)
            distractors = distractors[:3]
            while len(distractors) < 3:
                distractors.append("None of the above")

            options = [concept] + distractors[:3]
            random.shuffle(options)
            labeled_options = [f"{chr(65 + j)}) {opt}" for j, opt in enumerate(options)]
            correct_label = next(
                lbl for lbl, opt in zip(labeled_options, options) if opt == concept
            )

            questions.append(
                {
                    "question": "Which of the following is discussed in the text?",
                    "options": labeled_options,
                    "correct_answer": correct_label,
                }
            )

        return questions[:num_questions]

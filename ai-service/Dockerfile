FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# 1. Install CPU-only torch first (separate index to avoid pulling GPU version)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 2. Install all other deps (incl. transformers, spaCy, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# 3. Re-ensure transformers is present (torch install can sometimes conflict)
RUN pip install --no-cache-dir transformers==4.41.2

# 4. spaCy model
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# 5. Pre-download the Flan-T5 model so first API call is fast
RUN python -c "from transformers import pipeline; pipeline('text2text-generation', model='google/flan-t5-base')"

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

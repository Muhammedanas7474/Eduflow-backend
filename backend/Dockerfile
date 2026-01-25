FROM python:3.13-slim

# Prevent python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure logs are shown immediately
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy backend code
COPY . .

EXPOSE 8000

# Default command (will be overridden for celery)
# CMD ["gunicorn", "eduflow.wsgi:application", "--bind", "0.0.0.0:8000"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

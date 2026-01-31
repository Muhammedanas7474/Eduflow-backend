FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# IMPORTANT: use daphne, not runserver
CMD ["daphne", "-b", "0.0.0.0", "-p", "8001", "realtime_service.asgi:application"]

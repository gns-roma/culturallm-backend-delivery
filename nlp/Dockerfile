FROM python:3.12-slim

WORKDIR /nlp

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY nlp.py .
COPY models.py .

EXPOSE 8004
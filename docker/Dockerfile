FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-deu \
    tesseract-ocr-nor \
    tesseract-ocr-spa \
    tesseract-ocr-nld \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY run.py .

# Create default .env if not exists
RUN touch .env

ENV FLASK_APP=run.py
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

EXPOSE 5000

# Execute the script content directly
CMD ["/bin/sh", "-c", "until PGPASSWORD=postgres psql -h db -U postgres -c '\\q'; do echo 'Postgres is unavailable - sleeping'; sleep 1; done; echo 'Postgres is up - executing command'; flask run --host=0.0.0.0 --debug"]

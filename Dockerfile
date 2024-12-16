FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=run.py
ENV FLASK_ENV=development

EXPOSE 5000

CMD ["sh", "-c", "./wait-for-db.sh db \"flask run --host=0.0.0.0\""]
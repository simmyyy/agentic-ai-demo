FROM python:3.12-slim

ARG AWS_REGION=us-east-2
ENV AWS_REGION=${AWS_REGION}
ENV AWS_DEFAULT_REGION=${AWS_REGION}

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn boto3

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

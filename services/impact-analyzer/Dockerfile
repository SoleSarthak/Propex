FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY services/impact-analyzer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the scoring-engine ML library built in Phase 1
COPY libs/scoring-engine /libs/scoring-engine
RUN pip install --no-cache-dir -e /libs/scoring-engine

# Copy shared library
COPY libs/python-shared /libs/python-shared
RUN pip install --no-cache-dir -e /libs/python-shared

# Copy the service code
COPY services/impact-analyzer/src ./src

EXPOSE 8005

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005"]

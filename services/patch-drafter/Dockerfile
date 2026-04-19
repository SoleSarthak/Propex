FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY services/patch-drafter/requirements.txt .
COPY libs/python-shared /libs/python-shared

# Install build tools, then all dependencies, then the shared library
RUN pip install --no-cache-dir setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e /libs/python-shared

# Copy the service code
COPY services/patch-drafter/src ./src

EXPOSE 8007

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8007"]

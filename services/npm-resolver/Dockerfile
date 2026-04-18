FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy shared libraries
COPY libs/python-shared /libs/python-shared
COPY libs/scoring-engine /libs/scoring-engine

# Copy service requirements
COPY services/npm-resolver/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service source code
COPY services/npm-resolver/src ./src

# Expose port
EXPOSE 8001

# Run the service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]

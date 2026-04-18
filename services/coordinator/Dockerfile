FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy shared libraries
COPY libs/python-shared /libs/python-shared
COPY libs/scoring-engine /libs/scoring-engine

# Install shared libraries
RUN pip install --no-cache-dir /libs/python-shared
RUN pip install --no-cache-dir /libs/scoring-engine

# Copy service requirements
COPY services/coordinator/requirements.txt .

# Install service dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service source code
COPY services/coordinator/src ./src

# Expose port
EXPOSE 8002

# Run the service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]

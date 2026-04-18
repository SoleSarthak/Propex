FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if necessary (lxml needs some c libraries sometimes)
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev libxml2-dev libxslt-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/maven-resolver/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared library and install it
COPY libs/python-shared /libs/python-shared
RUN pip install --no-cache-dir -e /libs/python-shared

# Copy the service code
COPY services/maven-resolver/src ./src

# Expose the service port
EXPOSE 8004

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"]

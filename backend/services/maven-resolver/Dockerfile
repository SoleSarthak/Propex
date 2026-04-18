FROM python:3.12-slim

WORKDIR /app

# Copy shared libraries and install them
COPY libs/python-shared /app/libs/python-shared
COPY services/maven-resolver /app/services/maven-resolver

WORKDIR /app/services/maven-resolver
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/services/maven-resolver/src:/app/libs/python-shared
CMD ["python", "src/main.py"]

FROM python:3.12-slim

WORKDIR /app

# Copy shared libraries and install them
COPY libs/python-shared /app/libs/python-shared
COPY services/pypi-resolver /app/services/pypi-resolver

WORKDIR /app/services/pypi-resolver
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/services/pypi-resolver/src:/app/libs/python-shared
CMD ["python", "src/main.py"]

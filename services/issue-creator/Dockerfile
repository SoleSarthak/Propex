FROM python:3.12-slim

WORKDIR /app

COPY services/issue-creator/requirements.txt .
# Install build tools, then dependencies and shared library
RUN pip install --no-cache-dir setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e /libs/python-shared

COPY services/issue-creator/src ./src

EXPOSE 8008

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8008"]

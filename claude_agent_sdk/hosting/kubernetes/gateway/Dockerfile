FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching — only re-run when requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (flat layout — no sub-packages)
COPY main.py k8s.py proxy.py ./

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

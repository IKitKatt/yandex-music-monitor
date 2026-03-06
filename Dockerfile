FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 monitor && \
    mkdir -p /app/data /app/logs && \
    chown -R monitor:monitor /app
USER monitor

CMD ["python", "main.py"]

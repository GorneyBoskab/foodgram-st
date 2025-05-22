FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc

COPY . .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

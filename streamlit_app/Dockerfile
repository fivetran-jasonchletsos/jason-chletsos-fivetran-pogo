FROM python:3.12-slim

WORKDIR /app

# Install nginx and supervisor to run both processes
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source and Streamlit config
COPY app.py .
COPY .streamlit/ .streamlit/

# nginx config — proxies port 8080 → Streamlit on 8501
# Explicitly handles WebSocket upgrade for /_stcore/stream
COPY nginx.conf /etc/nginx/nginx.conf

# supervisor config — starts both nginx and streamlit
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8080

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

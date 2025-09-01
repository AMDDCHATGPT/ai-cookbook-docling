FROM python:3.11-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements file first for better caching
COPY knowledge/docling/requirements.txt .

# Install Python dependencies
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt

# Copy application code
COPY knowledge/docling/ ./knowledge/docling/

# Set Streamlit configuration for headless operation
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Set default port for Cloud Run
ENV PORT=8080

# Start Streamlit app
ENTRYPOINT ["sh", "-c", "streamlit run knowledge/docling/5-chat.py --server.port $PORT --server.address 0.0.0.0"]
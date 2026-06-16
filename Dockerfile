FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install dependencies in editable mode
RUN pip install --no-cache-dir -e .

# Expose Streamlit default port for Hugging Face
EXPOSE 7860

# Ensure start.sh has execute permissions
RUN chmod +x start.sh

# Run the startup script
CMD ["./start.sh"]

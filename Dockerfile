# Use a minimal Python image
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

# Install Fish shell and other basic dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    pandoc \
    fish \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install -r requirements.txt

# Set Fish as the default shell
SHELL ["/usr/bin/fish", "-c"]

# Set the working directory
WORKDIR /app

EXPOSE 8000

CMD ["mkdocs", "serve", "--dev-addr", "0.0.0.0:8000"]

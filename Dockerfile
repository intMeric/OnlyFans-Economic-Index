# Use Selenium standalone Chrome image as base
FROM selenium/standalone-chrome

# Switch to root to install Python and dependencies
USER root

# Install Python 3.12 and pip
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python3 to point to Python 3.12
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# Install UV package manager
RUN python3 -m pip install uv

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy UV configuration files and required metadata files
COPY pyproject.toml LICENSE README.md ./

# Create virtual environment and install dependencies
RUN uv venv .venv --python python3.12 \
    && . .venv/bin/activate \
    && uv pip install httpx>=0.28.1 asyncpg>=0.29.0 selenium>=4.0.0 webdriver-manager>=4.0.2

# Copy source code
COPY src/ ./src/
COPY Makefile ./

# Install the local package in editable mode
RUN . .venv/bin/activate && uv pip install -e .

# Ensure the virtual environment is activated for all commands
ENV PATH="/app/.venv/bin:$PATH"

# Create directories for mounted volumes
RUN mkdir -p /app/data /app/config

# Set Chrome binary path for Selenium
ENV CHROME_BIN=/usr/bin/google-chrome


# Expose port if needed (optional)
# EXPOSE 8000

# Default command - use python directly from venv
ENTRYPOINT ["python", "-m", "onlyfans_economic_index.main"]
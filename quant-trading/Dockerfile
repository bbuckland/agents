FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY quant_trading/ quant_trading/

# Expose API port
EXPOSE 8000

# Run API server
CMD ["uv", "run", "uvicorn", "quant_trading.api:app", "--host", "0.0.0.0", "--port", "8000"]

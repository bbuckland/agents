FROM ghcr.io/openclaw/openclaw:latest

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    gh \
    && rm -rf /var/lib/apt/lists/*

# Install npm-based CLIs
RUN npm install -g @steipete/summarize

# Switch back to node user
USER node

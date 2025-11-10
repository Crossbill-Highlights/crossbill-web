# Stage 1: Build frontend
FROM node:24-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source (including pre-generated API client)
COPY frontend/ ./

# Build frontend for production
# Set VITE_API_URL to empty string so it uses relative paths (same origin)
# Skip API generation since we copy the pre-generated files
ENV VITE_API_URL=""
RUN npm run routes:generate && npx tsc && npx vite build

# Stage 2: Setup backend and serve everything
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency installation
RUN pip install --no-cache-dir uv

# Copy backend dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Export dependencies to requirements.txt and install
# This works with package-mode = false
RUN uv export --no-dev --no-hashes --no-emit-project -o requirements.txt && \
    uv pip install --system --no-cache -r requirements.txt

# Copy backend source code
COPY backend/crossbill ./crossbill
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist ./static

# Create directory for book covers
RUN mkdir -p /app/book-covers

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Run database migrations and start uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn crossbill.main:app --host 0.0.0.0 --port ${PORT}"]

# Stage 1: Build the frontend
FROM node:18-alpine AS builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps

COPY frontend/ .
RUN npm run build

# Stage 2: Final image with backend and frontend served
FROM python:3.11-slim
WORKDIR /app

# Install dependencies: Python requirements, Nginx, and supervisord
RUN apt-get update && apt-get install -y --no-install-recommends nginx supervisor && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and configs
COPY backend/ ./backend/
COPY config/ ./config/

# Copy built frontend from the builder stage
COPY --from=builder /app/frontend/dist /var/www/html

# Copy Nginx and supervisord configurations
COPY nginx.conf /etc/nginx/sites-available/default
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 80 19002

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

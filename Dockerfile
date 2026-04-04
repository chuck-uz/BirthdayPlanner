# Единый Dockerfile: backend (FastAPI) и frontend (Vite/React).
# Сборка: docker compose build
# Вручную: docker build --target backend -t bp-api .
#          docker build --target frontend-development -t bp-fe .
# Прод-статика: docker build --target frontend-production -t bp-fe-static .

# --- Backend ---
FROM python:3.12-alpine AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apk add --no-cache \
    libjpeg-turbo \
    freetype

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- Frontend: зависимости ---
FROM node:20-alpine AS frontend-deps

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# --- Frontend: production build ---
FROM node:20-alpine AS frontend-builder

WORKDIR /app

COPY --from=frontend-deps /app/node_modules ./node_modules
COPY frontend/package.json frontend/package-lock.json ./
COPY frontend/ .

ARG VITE_TELEGRAM_BOT_NAME
ARG VITE_TELEGRAM_AUTH_URL
ARG VITE_API_PROXY_TARGET
ENV VITE_TELEGRAM_BOT_NAME=$VITE_TELEGRAM_BOT_NAME \
    VITE_TELEGRAM_AUTH_URL=$VITE_TELEGRAM_AUTH_URL \
    VITE_API_PROXY_TARGET=$VITE_API_PROXY_TARGET

RUN npm run build

FROM nginx:1.27-alpine AS frontend-production

COPY --from=frontend-builder /app/dist /usr/share/nginx/html
COPY frontend/nginx-docker.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# --- Frontend: Vite dev (docker compose) ---
FROM node:20-alpine AS frontend-development

WORKDIR /app

ENV NODE_ENV=development

COPY --from=frontend-deps /app/node_modules ./node_modules
COPY frontend/package.json frontend/package-lock.json ./
COPY frontend/ .

EXPOSE 5173

ENV HOST=0.0.0.0

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

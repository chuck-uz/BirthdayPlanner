# Vite 8 + React 19 + TypeScript (package.json: dev — vite; build — tsc -b && vite build).
# По умолчанию — development (совместимо с docker-compose: HMR, прокси /api).

FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# Статика + nginx (легкий образ). Сборка: docker build --target production ./frontend
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY package.json package-lock.json ./
COPY . .

ARG VITE_TELEGRAM_BOT_NAME
ARG VITE_TELEGRAM_AUTH_URL
ARG VITE_API_PROXY_TARGET
ENV VITE_TELEGRAM_BOT_NAME=$VITE_TELEGRAM_BOT_NAME \
    VITE_TELEGRAM_AUTH_URL=$VITE_TELEGRAM_AUTH_URL \
    VITE_API_PROXY_TARGET=$VITE_API_PROXY_TARGET

RUN npm run build

FROM nginx:1.27-alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx-docker.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# Dev-сервер (цель по умолчанию для docker compose build frontend)
FROM node:20-alpine AS development

WORKDIR /app

ENV NODE_ENV=development

COPY --from=deps /app/node_modules ./node_modules
COPY package.json package-lock.json ./
COPY . .

EXPOSE 5173

ENV HOST=0.0.0.0

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# FastAPI + async SQLAlchemy. Pillow/cryptography ставятся из готовых wheels (musllinux) под Alpine.
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Runtime-библиотеки для Pillow (JPEG/FreeType)
RUN apk add --no-cache \
    libjpeg-turbo \
    freetype

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Миграции БД (Alembic)

Схема управляется Alembic. Приложение больше **не** создаёт таблицы при старте.

## Обычный запуск

Контейнер `backend` сам выполняет `alembic upgrade head` (см. `entrypoint.sh`).
Вручную:

```bash
cd backend
alembic upgrade head
```

## ⚠️ Существующая БД (таблицы уже созданы прежним `create_all`)

Первый переход на Alembic на уже работающей базе: НЕ запускайте `upgrade` вслепую —
он попытается создать существующие таблицы и упадёт. Пометьте схему как актуальную:

```bash
cd backend
alembic stamp head
```

После этого дальнейшие `alembic upgrade head` работают штатно.

## Новая миграция

```bash
cd backend
alembic revision --autogenerate -m "краткое описание"
# проверьте сгенерированный файл в migrations/versions/, затем:
alembic upgrade head
```

`env.py` берёт `DATABASE_URL` и метаданные из приложения — отдельная настройка не нужна.

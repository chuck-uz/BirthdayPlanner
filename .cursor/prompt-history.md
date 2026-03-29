# Журнал запросов и решений (BirthdayPlanner)

Читать перед работой; дополнять после каждой **законченной** задачи по запросу пользователя. Секреты не записывать.

---

### 2026-03-29 — Стартовое наполнение (сессия до текущего правила)

- **Запрос (суть):** Проект BirthdayPlanner: FastAPI + Postgres + Docker; фронт Vite/React/Telegram Login; правила `.cursorrules` / `.mdc`; исправления авторизации и прокси.
- **Сделано:**
  - Правила: `.cursor/rules/birthday-planner-*.mdc`, `.cursorrules`; позже **`birthday-planner-auth.mdc`** с деталями auth.
  - **TelegramAuth:** `postMessage` убран; popup успех → редирект в том же окне (`location.replace`); слушатель `message` удалён; подсказка про переключение вкладки / refresh; убран `request_access: write`; доверие к `e.origin` / same-tab fallback ранее.
  - **Backend `GET /api/auth/telegram`:** обязателен **`response_model=None`** (иначе FastAPI падает при старте → Docker backend restart → **502**).
  - **Vite:** `process.env.VITE_API_PROXY_TARGET`, `resolveApiProxyTarget` (хост `backend` → `127.0.0.1` вне Docker), `envDir` по наличию `.env` в родителе `frontend/`; compose: **`IN_DOCKER=1`** для frontend.
  - **AuthContext / api:** `validateStatus` 200|401 для `/api/users/me`; интерцептор не зовёт `notifyUnauthorized` на этот путь.
  - Документация симптомов: 502 / 401 / postMessage Firefox.
- **Итог для следующих сессий:** Не возвращать `postMessage` для popup-успеха без явного запроса; помнить `response_model=None` на telegram route; прокси и Docker — см. `birthday-planner-auth.mdc`.

### 2026-03-29 — Правило: журнал промтов и порядок работы

- **Запрос (суть):** Записывать правило: вести базу промтов, после каждого промта дополнять, при выполнении смотреть что уже сделано, без зацикливания и галлюцинаций.
- **Сделано:** Файл **`.cursor/rules/birthday-planner-agent-workflow.mdc`** (`alwaysApply: true`); журнал **`.cursor/prompt-history.md`**; обновлён **`.cursorrules`** (ссылка).
- **Итог для следующих сессий:** Перед задачей читать `prompt-history.md`; после задачи — новая секция в журнале; не повторять отклонённые решения из журнала.

### 2026-03-29 — Firefox postMessage на oauth.telegram.org; URL виджета на скрине «не наш»

- **Запрос (суть):** Скрин: ошибка postMessage `targetOrigin http://127.0.0.1` vs recipient `oauth.telegram.org`; в URL embed — `return_to` на фронт `5173/`, `request_access=write`, `size=medium` (не совпадает с актуальным кодом репо).
- **Сделано:** Основной вход — **`TelegramInlineWidget`**: официальный `telegram-widget.js` + `data-auth-url` = `buildReturnToUrl` на **бэкенд** (без `request_access`). URL-утилиты в **`frontend/src/lib/telegramLoginUrls.ts`**. **`TelegramAuth`:** сверху встроенный виджет, снизу запас — popup на oauth embed. Убрана кнопка «в этой вкладке» на чистый oauth-URL (она тоже ломалась).
- **Итог для следующих сессий:** Рекомендовать встроенный виджет; при скринах с чужими query — напоминать пересобрать фронт и проверить `VITE_TELEGRAM_AUTH_URL` (должен быть `:8000/.../telegram`, не `5173`).

### 2026-03-29 — Кнопка Telegram снова не грузится

- **Запрос (суть):** Кнопка входа снова не загружается.
- **Сделано:** `TelegramInlineWidget` переведён с **`telegram-widget.js` + useEffect** на **`<iframe src={buildTelegramOAuthEmbedUrl(..., false)}>`** + ссылка «открыть во вкладке»; причина — React **StrictMode** снимает DOM до async-отрисовки скрипта. Подсказка в UI про обновление вкладки после входа в iframe.
- **Итог для следующих сессий:** Не вставлять telegram-widget через effect без защиты от StrictMode; iframe или статический script в `index.html`.

### 2026-03-29 — Кнопка не отображается (iframe пустой)

- **Запрос (суть):** Кнопка Telegram снова не видна.
- **Сделано:** Проверка заголовков: **`Content-Security-Policy: frame-ancestors http://127.0.0.1`** у embed — родитель **`http://127.0.0.1:5173`** не проходит, iframe пустой. **`TelegramInlineWidget`** заменён на **стилизованную ссылку** `<a href={buildTelegramOAuthEmbedUrl(..., false)}>` (оранжевая кнопка). Тексты в UI и правилах обновлены.
- **Итог для следующих сессий:** Не встраивать oauth.telegram.org в iframe при dev на нестандартном порту; обход — ссылка/новая вкладка/порт 80 или прод-домен.

### 2026-03-29 — Нужно маленькое окно, не новая вкладка

- **Запрос (суть):** Основная кнопка открывает другую вкладку; нужно небольшое окно на этой вкладке (родитель остаётся).
- **Сделано:** Удалён **`TelegramInlineWidget.tsx`**. Основной CTA — снова **`Button` + `window.open(..., popup features)`** и **`buildTelegramOAuthEmbedUrl(..., true)`**. Запас — обычная ссылка «Открыть вход в этой вкладке» без `target="_blank"`. Файл компонента с ссылкой как «главная» кнопка убран.
- **Итог для следующих сессий:** Главный вход Telegram — только `window.open` с размерами; `<a>` — запас при блокировке popup.

### 2026-03-29 — postMessage Firefox «по кругу»

- **Запрос (суть):** Снова ошибка postMessage `http://127.0.0.1` vs `oauth.telegram.org`; ощущение хождения по кругу.
- **Сделано:** Подтверждено grep: в проекте **нет** `postMessage` в коде (только комментарий). Ошибка — **внутри Telegram**. Добавлен абзац на странице логина и блок в **`birthday-planner-auth.mdc`**: не пытаться бесконечно чинить нашим кодом; критерий успеха — редирект и cookie.
- **Итог для следующих сессий:** Различать шум консоли Telegram и баги нашего приложения.

### 2026-03-29 — Скрин: жёлтое про несколько popup + postMessage

- **Запрос (суть):** Скрин консоли (без нового текстового вопроса).
- **Сделано:** В UI и **`birthday-planner-auth.mdc`** добавлено объяснение жёлтого предупреждения Firefox про блокировку **нескольких** всплывающих окон (цепочка Telegram после нашего `window.open`); рекомендация — разрешить popup для `127.0.0.1` или «вход в этой вкладке».
- **Итог для следующих сессий:** Два разных сообщения в консоли: блокировка popup (мы можем подсказать настройки) и postMessage (скрипты Telegram).

### 2026-03-29 — postMessage при «Войти как Denis»: приоритет same-tab

- **Запрос (суть):** Снова ошибка postMessage при нажатии «Войти как Denis».
- **Сделано:** **Основной CTA** снова **оранжевая ссылка** — переход **в этой вкладке** (`buildTelegramOAuthEmbedUrl(..., false)`); «маленькое окно» — вторичная кнопка. Тексты и правила обновлены: same-tab уменьшает цепочку popup и часто консольные сбои Telegram.
- **Итог для следующих сессий:** Рекомендовать same-tab первым для Firefox/dev.

### 2026-03-29 — postMessage повторяется даже в этой вкладке

- **Запрос (суть):** Пользователь: ошибка postMessage `http://127.0.0.1` vs `https://oauth.telegram.org` повторяется.
- **Сделано:** На **`LoginPage`** добавлен заметный блок «Про красную строку в консоли Firefox»: это скрипт Telegram при localhost/порте, не приложение; критерий успеха — URL `http://127.0.0.1:8000/api/auth/telegram?…`; если редиректа нет — Chrome / защита от трекинга. В **`TelegramAuth`** подсказка обновлена: `postMessage` бывает и при оранжевой кнопке.
- **Итог для следующих сессий:** Same-tab не убирает консольный шум Telegram; не обещать «исправим postMessage» кодом репо.

### 2026-03-29 — Vite 127.0.0.1, normalize auth URL, CORS комментарий

- **Запрос (суть):** Зафиксировать dev-сервер на 127.0.0.1; callback Telegram — полный `http://127.0.0.1:8000/api/auth/telegram`; CORS с явным `127.0.0.1:5173` и напоминание про localhost vs 127.0.0.1.
- **Сделано:** **`vite.config.ts`:** `host: '127.0.0.1'` вне Docker, при `IN_DOCKER=1` — `true` (иначе порт из контейнера не пробросится). **`telegramLoginUrls.ts`:** `normalizeTelegramAuthBase` (localhost→127.0.0.1, корень URL → `/api/auth/telegram`). **`TelegramAuth`:** `return_to` строится от нормализованного URL. **`main.py`:** комментарий к `allow_origins` (разные origin).
- **Итог для следующих сессий:** В Docker фронт по-прежнему слушает 0.0.0.0 через CLI Dockerfile; на хосте открывать `http://127.0.0.1:5173`.

### 2026-03-29 — «Heavy Artillery»: script widget + data-onauth + data-origin; host 127.0.0.1

- **Запрос (суть):** Виджет через `document.createElement('script')`, `data-origin`, без `data-auth-url` — только `data-onauth` → JS-колбэк; `vite` `server.host` строго `'127.0.0.1'`.
- **Сделано:** **`TelegramAuth`:** контейнер + `useEffect`, скрипт `telegram-widget.js`, `data-onauth="__birthdayPlannerTelegramAuth(user)"`, `data-origin=window.location.origin`, без `data-auth-url`; колбэк → `buildTelegramAuthRedirectFromWidgetUser` → `location.assign` на бэкенд. Fallback — oauth-ссылка и popup. **`telegramLoginUrls.ts`:** `buildTelegramAuthRedirectFromWidgetUser`. **`vite.config.ts`:** `host: '127.0.0.1'` (Docker: переопределение через `CMD --host 0.0.0.0`).
- **Итог для следующих сессий:** При пустом виджете на `:5173` возможен прежний CSP `frame-ancestors`; оставлены fallback-ссылки.

### 2026-03-29 — Фронт в Docker на порту 80, CORS без порта, HMR

- **Запрос (суть):** `80:5173` в compose; Vite `hmr.clientPort: 80`; ссылки без `:5173`; CORS `http://127.0.0.1` без порта.
- **Сделано:** **`docker-compose.yml`:** `80:5173`, `HMR_CLIENT_PORT=80`, **`FRONTEND_DEFAULT_URL`** для backend в стеке. **`vite.config.ts`:** `hmr: { clientPort }` если задан `HMR_CLIENT_PORT`. **`config`/`redirects`:** дефолт фронта `http://127.0.0.1/`. **`main.py` CORS:** добавлены `http://127.0.0.1`, `http://localhost`; 5173/5174 оставлены для локального dev. **`telegramLoginUrls`:** `publicOrigin127ForHints`; **TelegramAuth/LoginPage**, **check-telegram-embed**, правила `.mdc`.
- **Итог для следующих сессий:** Локально без Docker HMR без `HMR_CLIENT_PORT`; на Windows порт 80 может требовать прав администратора.

### 2026-03-29 — Минимальный UI логина

- **Запрос (суть):** Синяя кнопка Telegram работает; убрать подсказки, альтернативные кнопки, Origin, блоки про Firefox/postMessage.
- **Сделано:** **`LoginPage`:** только заголовок, виджет, ссылка «На главную», переключатель темы. **`TelegramAuth`:** только script + data-onauth; при отсутствии env — «Вход недоступен». Удалены **`publicOrigin127ForHints`**, oauth/popup fallback из UI.

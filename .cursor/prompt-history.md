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

### 2026-03-29 — Визуал страницы логина

- **Запрос (суть):** Красивый фронт окна логина, не ломая авторизацию Telegram.
- **Сделано:** **`LoginPage`:** многослойный фон (градиенты, блобы, лёгкая сетка), карточка с градиентной обводкой и стеклом, иконка Send, заголовок «Добро пожаловать», короткий подзаголовок, спиннер в рамке, ссылка «На главную» с ArrowLeft; анимация **`bp-login-enter`** в **`index.css`**. **`TelegramAuth`:** без изменений в `useEffect`/скрипте; визуальная «ложка» под виджет; состояние без env — иконка ShieldOff + текст.
- **Итог для следующих сессий:** Логика виджета прежняя (`data-onauth`, `data-origin`, тот же глобальный колбэк).

### 2026-03-29 — Только реальные ДР на главной

- **Запрос (суть):** Убрать фейковые дни рождения; показывать реальных пользователей.
- **Сделано:** **`GET /api/users/birthdays/upcoming`** (auth): пользователи с `birth_date`, сортировка по дням до следующего ДР; **`birthday_utils.days_until_next_birthday`**, схема **`UpcomingBirthdayOut`**. **`HomePage`:** загрузка API, скелетоны, пустое состояние, карточки; **`birthdayFormat.ts`**. **`ProfilePage`:** вишлист без стартовых демо-пунктов, тексты без «демо».
- **Итог для следующих сессий:** Список = все пользователи БД с заполненной датой рождения (включая текущего).

### 2026-03-29 — Профиль именинника и вишлисты

- **Запрос (суть):** Проваливаться в профиль имениников и смотреть вишлисты.
- **Сделано:** **API:** `GET /api/users/{id}` (публичный профиль + вишлисты), `GET/POST/DELETE /api/users/me/wishlists`, схемы **`WishlistItemOut`**, **`WishlistCreate`**, **`UserPublicProfileOut`**. **`ProfilePage`:** вишлист с бэкенда. **`UserProfilePage`** `/users/:userId`, **`HomePage`:** карточки — ссылки. Роут в **`App.tsx`**.
- **Итог для следующих сессий:** Вишлист хранится в таблице `wishlists`; чужой профиль только на чтение.

### 2026-03-29 — Подписки на ДР, планировщик, Telegram

- **Запрос (суть):** Подписка «Уведомить меня», таблица subscriptions, событие с group_id/invite_link, ежедневно 09:00 за N дней до ДР — группа или рассылка; именинник не получает; проверка /start у бота после подписки.
- **Сделано:** **Модели:** `Subscription`, `BirthdayEvent` (уникальность target+дата празднования). **API:** `GET/POST/DELETE .../subscription`, `GET /me/telegram-delivery`. **telegram_service:** getChat, sendMessage, getMe, попытка createChat+exportChatInviteLink. **jobs:** `run_daily_birthday_reminders` (вызов за `BIRTHDAY_NOTIFY_DAYS_BEFORE`, по умолчанию **14**), APScheduler **09:00** `SCHEDULER_TIMEZONE`. **Фронт:** `BirthdayNotifyBell`, главная и профиль друга. Зависимости: **httpx**, **apscheduler**.
- **Итог для следующих сессий:** Обычный Bot API часто **не создаёт** группы — срабатывает **fallback** личными сообщениями; именинник исключён из подписчиков на себя.

### 2026-03-29 — Минимальный UI логина

- **Запрос (суть):** Синяя кнопка Telegram работает; убрать подсказки, альтернативные кнопки, Origin, блоки про Firefox/postMessage.
- **Сделано:** **`LoginPage`:** только заголовок, виджет, ссылка «На главную», переключатель темы. **`TelegramAuth`:** только script + data-onauth; при отсутствии env — «Вход недоступен». Удалены **`publicOrigin127ForHints`**, oauth/popup fallback из UI.

### 2026-03-29 — Правило: база «что уже сделано»

- **Запрос (суть):** Запомнить и записать в правила базу, куда смотреть, что уже сделано.
- **Сделано:** Файл **`.cursor/rules/birthday-planner-done-base.mdc`** (`alwaysApply: true`) — структурированный перечень реализованного функционала и ключевых путей; **`.cursorrules`** — строка в таблице; **`birthday-planner-agent-workflow.mdc`** — шаг 1 дополнен чтением done-base рядом с `prompt-history.md`.
- **Итог для следующих сессий:** Хронология — **`prompt-history.md`**; быстрый обзор возможностей репо — **`birthday-planner-done-base.mdc`**; при крупных фичах обновлять done-base.

### 2026-03-29 — После каждого промта: журнал + база

- **Запрос (суть):** Пополняй базу и правила после каждого промта пользователя.
- **Сделано:** **`birthday-planner-agent-workflow.mdc`:** пункт 2 расширен — всегда `prompt-history.md`; **`birthday-planner-done-base.mdc`** править при изменениях продукта/API/моделей/правил или строка в «Журнал обновлений базы»; иначе в журнале промта — *done-base без изменений*. **`birthday-planner-done-base.mdc`:** блок про документацию, таблица «Журнал обновлений базы». **`.cursorrules`** — напоминание в конце.
- **Итог для следующих сессий:** Выполнять обновление базы по смыслу промта; не раздувать done-base мелочами без изменения снимка.

### 2026-03-29 — Telegram при подписке: подтверждение и чат за 14 дней

- **Запрос (суть):** При подписке на уведомления — сообщение в бот «вы подписались»; если ДР именинника в пределах двух недель — если группа/событие уже есть, прислать ссылку; иначе создать группу (как планировщик) и прислать ссылку.
- **Сделано:** Модуль **`backend/birthday_notify_logic.py`** — тексты, `get_birthday_event`, `create_birthday_event_and_notify_subscribers`, `run_subscribe_telegram_followup` (окно = **`BIRTHDAY_NOTIFY_DAYS_BEFORE`**). **`jobs/birthday_notifications.py`** вызывает общую функцию. **`POST /api/users/{id}/subscription`:** после `flush` при **новой** подписке — Telegram followup; ошибки Telegram логируются, ответ API не падает.
- **Итог для следующих сессий:** Логика события/рассылки — в `birthday_notify_logic.py`; при повторном POST подписки повторных сообщений в бот нет.

### 2026-03-29 — Админ: запрос на группу, кнопки, вебхук

- **Запрос (суть):** За 14 дней до ДР — найти именинника и подписчиков; бот пишет только админу (`TELEGRAM_ADMIN_ID`) текст с количеством и кнопки «Создать группу» / «Пропустить»; по «Создать» — инструкция создать группу и добавить бота админом; после добавления бота в группу — invite link и рассылка подписчикам заданным текстом.
- **Сделано:** **`config`:** `TELEGRAM_ADMIN_ID`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_WEBHOOK_BASE_URL`. **`models.AdminBirthdayPrompt`**. **`birthday_admin_flow.py`**, **`routers/telegram_webhook.py`**. **`telegram_service`:** reply_markup, callback, edit markup, export link, get bot id, setWebhook. При заданном `TELEGRAM_ADMIN_ID` **`create_birthday_event_and_notify_subscribers`** не вызывает `createChat`, а **`ensure_admin_prompt_for_birthday`**. **`main`:** регистрация вебхука при старте если задан base URL. Текст подписчикам: **`message_gift_group_ready`**. Комментарий в **`docker-compose.yml`**.
- **Итог для следующих сессий:** Без вебхука и HTTPS кнопки не заработают; без `TELEGRAM_ADMIN_ID` сохраняется старый авто-`createChat`/fallback.

### 2026-03-29 — Убрать fallback «не удалось создать группу» в ЛС

- **Запрос (суть):** При подписке приходят подтверждение и ненужное сообщение про неудачный Bot API; нет запроса админу на группу.
- **Сделано:** **`birthday_notify_logic`:** при провале `createChat` без админа — **не** рассылать подписчикам fallback, **не** писать `BirthdayEvent`; лог warning с подсказкой про `TELEGRAM_ADMIN_ID`. **`send_event_summary_to_telegram_user`** шлёт только при реальной ссылке. **`config`:** пустой `TELEGRAM_ADMIN_ID` → `None`.
- **Итог для следующих сессий:** Запрос админу только если в `.env` задан числовой id и бэкенд перезапущен (`get_settings` кэшируется).

### 2026-03-29 — Запрос группы админу при подписке самого админа

- **Запрос (суть):** После «вы подписались» не приходит сообщение о создании группы; нужно, чтобы оно приходило и когда подписывается администратор.
- **Сделано:** **`ensure_admin_prompt_for_birthday`:** `session.flush()`, опционально **`trigger_subscriber`** (подмешивается в список подписчиков, если SELECT ещё не видит строку), **`relax_days_limit`**; в тексте админу — фактические дни до ДР. **`run_subscribe_telegram_followup`:** если `subscriber.telegram_id == TELEGRAM_ADMIN_ID`, цепочка группы/админа вызывается и **при днях > BIRTHDAY_NOTIFY_DAYS_BEFORE**. **`create_birthday_event_and_notify_subscribers`** пробрасывает `trigger_subscriber` / `relax_admin_days`; без админа — тот же merge для legacy `createChat`.
- **Итог для следующих сессий:** `TELEGRAM_ADMIN_ID` должен совпадать с `telegram_id` пользователя в БД (тот же аккаунт, что логинится в приложение).

### 2026-03-29 — Кнопки «создать группу» без TELEGRAM_ADMIN_ID

- **Запрос (суть):** Подписка на «Тестовый Тест» (ДР 03.04): приходит только «вы подписались», нет предложения создать группу.
- **Сделано:** Исправлена логика: **`ensure_admin_prompt_for_birthday` раньше сразу выходил, если `TELEGRAM_ADMIN_ID` пуст**; **`create_birthday_event` вызывал ручной поток только при заданном admin id** — в итоге без env шла ветка `createChat` и тишина. Теперь при **POST подписки** (`trigger_subscriber`) всегда включается ручной поток; получатель ЛС: **`TELEGRAM_ADMIN_ID` или, если не задан, `telegram_id` подписавшегося**. Поле **`AdminBirthdayPrompt.prompt_recipient_telegram_id`**, callback и **`my_chat_member`** завязаны на него. **`main`:** при Postgres `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
- **Итог для следующих сессий:** Если задан `TELEGRAM_ADMIN_ID`, кнопки уходят туда, а не подписчику (если это разные люди).

### 2026-03-29 — Админ не получал запрос: окно 14 дней и повторная отправка

- **Запрос (суть):** По-прежнему не приходит запрос админу на создание группы.
- **Сделано:** В **`run_subscribe_telegram_followup`** при заданном **`TELEGRAM_ADMIN_ID`** цепочка **`ensure_admin_prompt`** вызывается **при любой новой подписке**, без отсечения `days > BIRTHDAY_NOTIFY_DAYS_BEFORE` (раньше при подписке не-админа за >14 дней выходили до вызова). **`relax_admin_days`** для этого случая. **`ensure_admin_prompt`:** логи при ранних выходах; при **`prompt_sent`** и **`admin_prompt_message_id is None`** — повторная отправка в Telegram; **`logger.error`** если `sendMessage` не вернул message_id.
- **Итог для следующих сессий:** Админ должен написать боту /start; при ошибке API смотреть логи backend.

### 2026-03-29 — Текст подтверждения подписки с датой ДР

- **Запрос (суть):** В боте после подписки добавить дату дня рождения («… Тестовый Тест, которое будет [дата]»).
- **Сделано:** **`subscription_confirmation_text`** в **`birthday_notify_logic.py`:** дата в формате **ДД.ММ.ГГГГ**; при отсутствии `birth_date` — прежняя однострочная формулировка.
- **Итог для следующих сессий:** — *done-base без изменений.*

### 2026-03-29 — Подтверждение подписки: «который», дата ДР в текущем году

- **Запрос (суть):** Заменить «которое» на «который»; показывать не дату рождения из профиля, а день рождения в **текущем календарном году**.
- **Сделано:** **`_birthday_date_in_year`**, текст с **ДД.ММ.ГГГГ** где год = `today.year`; 29.02 → 28.02 в невисокосный год.
- **Итог для следующих сессий:** *done-base без изменений.*

### 2026-03-29 — Защищённые аватары (upload, JWT, Docker volume)

- **Запрос (суть):** Папка `uploads/avatars`, volume в compose, поле `avatar_path`, `PATCH /api/users/me/avatar`, `GET /api/users/{id}/avatar` с JWT, без StaticFiles на uploads.
- **Сделано:** **`backend/uploads/avatars/.gitkeep`**, **`avatar_storage.py`** (лимит 5 МБ, JPEG/PNG по magic + Content-Type, UUID-имя, защита путей), **`User.avatar_path`**, миграция **`ALTER users.avatar_path`** в **`main`**, **`ensure_avatars_dir`** при старте. Роуты в **`users.py`**; **`UserMeOut`:** `has_avatar`, `avatar_url`. Compose: **`backend_avatars:/app/uploads/avatars`**. **`python-multipart`**, **`.gitignore`** на файлы в avatars. Тип **`UserProfile`** на фронте расширен опциональными полями.
- **Итог для следующих сессий:** Выдача только через API; после `docker compose build` пересобрать backend для зависимостей.

### 2026-03-29 — Главная: карточки, Google Календарь, `is_bot_active` и модалка бота

- **Запрос (суть):** Прямоугольные карточки на главной (аватар, ФИО, дата); кнопки Профиль / Вишлист / Подписаться (колокольчик) / Google Календарь; на бэкенде `User.is_bot_active`, обновление при старте бота; на фронте при `is_bot_active === false` — модалка «запустите бота», подписка disabled; ссылка календаря с предзаполнением из карточки.
- **Сделано:**
  - **Backend:** `User.is_bot_active` (`Boolean`, default false), миграция в **`main.py`**; при личном **`/start`** в вебхуке — **`telegram_bot_start_handler.handle_telegram_message_for_bot_activity`**; **`GET /api/users/me/telegram-delivery`**: если `getChat` подтверждает доставку — выставить **`is_bot_active = True`**; **`UserMeOut.is_bot_active`**; **`UpcomingBirthdayOut.has_avatar`**; вебхук обрабатывает **`message`** (см. **`telegram_service.setWebhook`** `allowed_updates`).
  - **Frontend:** **`HomePage`** — макет карточки, ссылки на профиль и `#wishlist`, **`BirthdayNotifyBell`** с **`isBotActive`** и **`onOpenBotHint`**, **`BotStartModal`**, кнопка Google через **`buildGoogleCalendarBirthdayUrl`** / **`nextBirthdayGoogleDates`** в **`birthdayFormat.ts`**; после загрузки telegram-delivery — **`refreshUser()`**.
  - **`BirthdayNotifyBell`:** подписаться неактивна, если бот не «активен» и пользователь ещё не подписан; ссылка-текст на подсказку.
  - **`UserProfilePage`:** тот же **`BotStartModal`** / **`isBotActive`**, **`refreshUser`** после delivery; у карточки вишлиста **`id="wishlist"`** + **`scroll-mt-24`** для якоря с главной.
  - **Типы:** **`UserProfile.is_bot_active`** в **`types/user.ts`**.
- **Итог для следующих сессий:** Подписка на уведомления по UX завязана на **`me.is_bot_active`**; флаг поднимается **`/start`** у бота или успешным **`getChat`** на delivery; календарь — только клиентская ссылка на `calendar.google.com` с `action=TEMPLATE`.

### 2026-03-29 — Вишлист с фото референса (карточки, Pillow, защищённая выдача)

- **Запрос (суть):** Пункты вишлиста как карточки «как в магазине»: название, описание, ссылка, опциональное фото; хранение в **`uploads/wishlist/`**, выдача только по API с JWT; сжатие изображений до 800px (**Pillow**); модалка добавления/редактирования с превью на фронте.
- **Сделано:**
  - **Backend:** модель **`Wishlist`**: **`description`**, **`link_url`**, **`photo_path`**; **`ALTER wishlists`** в **`main.py`**; **`wishlist_storage.py`** (валидация JPEG/PNG, 5 МБ, ресайз, UUID-имена); **`POST/PATCH /api/users/me/wishlists`** — **`multipart/form-data`**, **`PATCH`** с **`clear_photo`**; **`GET /api/wishlists/{item_id}/photo`** — роутер **`routers/wishlists.py`**; удаление файла при **DELETE** и замене фото; зависимость **`pillow`**; volume **`backend_wishlist_photos`** в compose; **`schemas/wishlist`**: **`WishlistItemOut`**, **`build_wishlist_item_out`**, **`parse_optional_link_url`** (**`HttpUrl`**).
  - **Frontend:** **`WishlistItemCard`**, **`WishlistItemModal`**, **`wishlistPhotoUrl`**; **`ProfilePage`** / **`UserProfilePage`**; тип **`WishlistItem`** с **`has_photo`**, **`description`**, **`link_url`**; внешние ссылки **«Где купить»** с **`noopener noreferrer`**.
- **Итог для следующих сессий:** Старый JSON-only **`POST …/wishlists` с `{title}`** заменён на **multipart**; фото вишлиста не отдаются через StaticFiles — только **`/api/wishlists/{id}/photo`**; после обновления бэкенда нужны **Pillow** и том **`wishlist`** в Docker.

### 2026-03-29 — Настройки профиля /profile/settings, Toast, аватар с камерой

- **Запрос (суть):** Полноценное редактирование ФИО и даты на отдельной странице (не **`/setup-profile`**); навигация «Настройки» в шапке; после сохранения toast и остаться на странице; аватар только на **`/profile`** — иконка камеры на превью.
- **Сделано:** **`ProfileSettingsPage`**, роут **`/profile/settings`**, **`ToastProvider`** + **`useToast`**, пункт в **`AppShell`**; **`profileValidation.ts`** общий с **`SetupProfilePage`**; **`ProfilePage`**: камера на аватаре, ссылка на настройки вместо **`/setup-profile`** для ФИО/даты; **`PATCH /api/users/me`**: явный **`Depends(get_db)`** + **`flush`**. Валидация «дата не в будущем» уже в **`UserProfileUpdate`** на бэкенде.
- **Итог для следующих сессий:** **`/setup-profile`** — только первичный вход; правки после регистрации — **`/profile/settings`**.

### 2026-03-29 — Админ: блокировка, список пользователей, правка данных

- **Запрос (суть):** Администратор: блокировать пользователей, менять данные, смотреть профили, полный контроль.
- **Сделано:** Поле **`User.is_blocked`**, **`403 account_blocked`** в **`get_current_user`**; **`TELEGRAM_ADMIN_ID`** определяет **`is_admin`** в **`UserMeOut`** и доступ к **`/api/admin/*`** (**`get_current_admin`**). Эндпоинты: список/карточка пользователя (вишлист, счётчики подписок), **`PATCH`** (ФИО, дата, блокировка; нельзя заблокировать себя), **`DELETE`** пункта вишлиста. Заблокированные исключены из **`birthdays/upcoming`**, ежедневных напоминаний, скрыты в **`GET /users/{id}`**, подписках, аватаре и фото вишлиста (админ видит). Фронт: **`/admin`**, **`/admin/users/:id`**, пункт «Админ» в шапке, **`notifyAccountBlocked`** / баннер на логине.
- **Итог для следующих сессий:** Без **`TELEGRAM_ADMIN_ID`** в `.env` админки нет; ID должен совпасть с **`telegram_id`** учётки в БД.

### 2026-03-29 — Админ: ожидание ссылки вместо кнопок создания группы

- **Запрос (суть):** Убрать кнопки «✅ Создать группу / ❌ Пропустить» в `birthday_admin_flow.py` и перейти в сценарий: админ присылает URL, после чего появляется кнопка рассылки подписчикам.
- **Сделано:** `backend/birthday_admin_flow.py`: режимы `STATE_AWAIT_LINK` / `STATE_LINK_RECEIVED`, обработчик `handle_telegram_admin_birthday_prompt_message`, новая callback-кнопка `bd_g:<prompt_id>` и рассылка с паузой `asyncio.sleep(0.05)`; `backend/routers/telegram_webhook.py` — подключение message-хендлера; `telegram_webhook` при `TELEGRAM_ADMIN_ID` обновляет старые сообщения, если они ещё с кнопками.
- **Итог для следующих сессий:** Для новых промптов в `TELEGRAM_ADMIN_ID` кнопок нет: «ожидаю ссылку» → админ отправляет URL → появляется «Разослать подписчикам».

### 2026-03-29 — Админ: тестовые пользователи из фронта

- **Запрос (суть):** Дать администратору возможность создавать тестовых пользователей из меню админки.
- **Сделано:** `backend/models.py` + `main.py`: поле `User.is_test`; `POST /api/admin/users/test` (только админ) создаёт синтетические аккаунты; `frontend/src/pages/AdminUsersPage.tsx` добавлена секция «Тестовые пользователи» (input count 1–20 + создание), тип в таблице + бейдж; `frontend/src/pages/AdminUserDetailPage.tsx` — пояснение для тестовых.
- **Итог для следующих сессий:** Только админ видит секцию; тестовые записи имеют синтетический `telegram_id` и пометку `is_test`.

### 2026-03-29 — Веб-админка рассылок /admin/dashboard + напоминание админу в Telegram

- **Запрос (суть):** Сделать единый админ-сценарий рассылок через фронт: `GET /api/admin/birthdays`, `POST /api/admin/broadcast-link`, защищённый `/admin/dashboard`, модалка с URL, статус «Отправлено», валидация `https://t.me/...`, кнопка «Админ-панель» в профиле; убрать предыдущие варианты рассылок; напоминать админу в Telegram за 14 дней.
- **Сделано:**  
  - **Backend:** добавлен alias-зависимость `get_admin_user`; новые схемы `AdminBirthdayDashboardItemOut`, `AdminBroadcastLinkIn/Out`; эндпоинты `GET /api/admin/birthdays` (сортировка по ближайшему ДР, `subscribers_count`, `status`) и `POST /api/admin/broadcast-link` (исключает именинника, отправляет подписчикам ссылку и кнопку, `sleep(0.05)`, фиксирует `BirthdayEvent`).  
  - **Scheduler/логика:** `jobs/birthday_notifications.py` в режиме `TELEGRAM_ADMIN_ID` шлёт админу Telegram-напоминание за 14 дней с переходом в `/admin/dashboard`; `birthday_notify_logic.py` отключает старый Telegram-поток ручных кнопок при наличии admin id, чтобы не дублировать веб-рассылку.  
  - **Frontend:** новая страница `frontend/src/pages/AdminDashboardPage.tsx`; роуты `/admin/dashboard` и `/admin/users`; `/admin` редиректит на dashboard; модалка рассылки, фронтовая валидация `https://t.me/...`, toast об успехе, колонка статуса; в `ProfilePage` добавлена ссылка «Админ-панель» только для `user.is_admin`.
- **Итог для следующих сессий:** Основной путь рассылок — только `/admin/dashboard`; Telegram-напоминание админу остаётся, старые телеграм-кнопочные варианты для админа больше не используются.

### 2026-03-29 — Админ: вкладки «Рассылки / Пользователи», блокировка из списка

- **Запрос (суть):** Дополнительная вкладка в админ-панели для управления пользователями (блокировка/разблокировка).
- **Сделано:** `frontend/src/components/admin/AdminLayout.tsx` — вкладки **Рассылки** (`/admin/dashboard`) и **Пользователи** (`/admin/users`); в `App.tsx` вложенный роут `/admin` с `Outlet`. На `AdminUsersPage` — кнопки **Заблокировать / Разблокировать** (`PATCH /api/admin/users/{id}`), для своей строки — disabled + toast; после успеха — обновление списка.
- **Итог для следующих сессий:** Админка единая: переключение вкладок сверху; деталь пользователя — `/admin/users/:id`.

### 2026-03-29 — Удаление всех тестовых пользователей

- **Запрос (суть):** Удалить всех тестовых пользователей.
- **Сделано:** `DELETE /api/admin/users/test` — удаляет всех с `is_test=true`, перед удалением снимает файлы вишлиста и аватара; ответ `{ deleted_count }`. На вкладке **Пользователи** кнопка «Удалить всех тестовых» с подтверждением.
- **Итог для следующих сессий:** Массовое удаление только через админ API/UI; связанные строки в БД уходят по CASCADE.

### 2026-03-29 — Удаление всех профилей пользователей (админ)

- **Запрос (суть):** Добавить функционал удаления всех профилей пользователей, не только тестовых, только для администратора.
- **Сделано:** `DELETE /api/admin/users/all` (только админ): удаляет все профили пользователей, предварительно очищает файлы вишлистов/аватаров; ответ `{ deleted_count, deleted_self }`. На вкладке **Пользователи** добавлен блок «Опасная зона» и кнопка «Удалить всех пользователей» с подтверждением; если удалён текущий админ — logout и переход на `/login`.
- **Итог для следующих сессий:** Полное удаление всех профилей запускается только вручную из опасной зоны или через новый админ endpoint.

### 2026-03-29 — Удаление пользователей по одному (без массового удаления)

- **Запрос (суть):** Убрать кнопку «удалить всех пользователей»; оставить удаление профиля по одному для каждого пользователя в списке.
- **Сделано:** Удалён массовый endpoint `DELETE /api/admin/users/all` и UI «Опасная зона». Добавлен `DELETE /api/admin/users/{id}` (только админ, нельзя удалить себя, удаляет файлы аватара/вишлистов). На `AdminUsersPage` в таблице добавлена колонка «Удаление» с кнопкой `Удалить` напротив каждого пользователя.
- **Итог для следующих сессий:** Удаление профилей выполняется только точечно из таблицы пользователей.

### 2026-04-04 — Dockerfile на Alpine, оптимизация образов

- **Запрос (суть):** Сгенерировать Dockerfile с учётом `package.json`, лёгкие образы на базе Alpine.
- **Сделано:** **`backend/Dockerfile`** — `python:3.12-alpine`, runtime `libjpeg-turbo`/`freetype` для Pillow, pip без кэша; **`backend/.dockerignore`**. **`frontend/Dockerfile`** — стадия **deps** + **development** по умолчанию (как compose: `npm run dev` + Vite); стадии **builder** + **production** (`nginx:1.27-alpine`, `npm run build`, **`frontend/nginx-docker.conf`** — SPA + прокси `/api/` на `backend:8000`); опциональные build-arg для `VITE_*`. Проверка: `docker build` backend и frontend (default и `--target production`).
- **Итог для следующих сессий:** Compose собирает dev-фронт; прод-статика — см. корневой `Dockerfile`, target **`frontend-production`**.

### 2026-04-04 — Один Dockerfile в корне для фронта и бэка

- **Запрос (суть):** Единый файл в корне для backend и frontend.
- **Сделано:** Корневой **`Dockerfile`** (targets **`backend`**, **`frontend-development`**, **`frontend-production`**), **`docker-compose.yml`** — `context: .`, `target` для сервисов; **`/.dockerignore`**. Удалены **`backend/Dockerfile`**, **`frontend/Dockerfile`**, локальные **`.dockerignore`** в подпапках. Прод-образ фронта: `docker build --target frontend-production .`
- **Итог для следующих сессий:** Сборка только из корня репозитория; отдельные Dockerfiles в `backend/`/`frontend/` больше не используются.

### 2026-07-10 — Аудит и рефакторинг (архитектура, безопасность, производительность)

- **Запрос (суть):** Провести глубокое код-ревью и внести все исправления.
- **Сделано (backend):**
  - **Alembic** вместо `create_all` + ручных `ALTER ... IF NOT EXISTS` в lifespan. `backend/alembic.ini`, `backend/migrations/env.py` (async), baseline `migrations/versions/0001_baseline.py` (совпадает с моделями — проверено autogenerate). Контейнер прогоняет `alembic upgrade head` через `backend/entrypoint.sh`. Для существующих БД — один раз `alembic stamp head` (см. `backend/migrations/README.md`).
  - **Единое хранилище изображений** `backend/storage/image_store.py` (`ImageStore`, `avatar_store`, `wishlist_store`) вместо продублированных `avatar_storage.py`/`wishlist_storage.py` (удалены). Пережатие через Pillow + `Image.MAX_IMAGE_PIXELS` (защита от decompression bomb); аватары теперь тоже переэнкодятся (снимается EXIF).
  - **B1:** `handle_telegram_admin_birthday_prompt_message` подключён к вебхуку (приём ссылки от админа в ЛС работал вхолостую).
  - **B4:** ссылка на группу хранится в БД (`AdminBirthdayPrompt.pending_invite_link`), а не в памяти процесса — переживает рестарт/несколько воркеров.
  - **B5:** удалён мёртвый `try_create_birthday_group` (метод `createChat` ботам недоступен).
  - **B2:** админ-дашборд `/api/admin/birthdays` — устранён N+1 (GROUP BY + выборка событий одним запросом).
  - **B3:** рассылка после подписки — в `BackgroundTasks`; `can_receive_bot_messages` берётся из кэша `is_bot_active` (без живого `getChat` на каждый запрос).
  - **B6:** CORS-origin из `CORS_ALLOW_ORIGINS` (список через запятую).
  - **B8:** вебхук возвращает 500 при ошибке обработчика (Telegram повторит доставку).
  - **B9:** rate limiting (slowapi) на логин, подписку, загрузку аватара/вишлиста.
  - Мелочи: `telegram_send_message` — тонкая обёртка над `..._message_id`; хардкод `14` → `birthday_notify_days_before`; несколько `assert` → явные проверки; `Cache-Control` на выдаче аватаров/фото.
  - **Тесты:** `backend/tests/` (pytest) для `auth`, `birthday_utils`, `redirects` — 16 тестов, зелёные. `requirements-dev.txt`, `pytest.ini`.
- **Сделано (frontend):** `AuthContext` — троттлинг авто-refresh на focus/visibilitychange (не дёргает `/api/users/me` дважды).
- **Итог для следующих сессий:** Схема БД — только через Alembic (`alembic revision --autogenerate`, затем `upgrade head`). Работа с файлами изображений — через `storage.image_store`. Новые чувствительные эндпоинты — под `@limiter.limit(...)`.

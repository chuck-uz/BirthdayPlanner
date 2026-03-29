type Props = {
  open: boolean
  onClose: () => void
  botUsername: string | null
}

export function BotStartModal({ open, onClose, botUsername }: Props) {
  if (!open) return null
  const href = botUsername ? `https://t.me/${botUsername}` : undefined

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="bot-start-title"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/50 backdrop-blur-[2px]"
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div className="relative z-10 w-full max-w-md rounded-2xl border border-zinc-200/80 bg-white p-6 shadow-xl dark:border-zinc-700 dark:bg-zinc-900">
        <h2 id="bot-start-title" className="text-lg font-semibold text-zinc-900 dark:text-white">
          Запустите бота
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
          Чтобы получать уведомления о днях рождения, нажмите «Старт» в нашем Telegram-боте.
        </p>
        {href ? (
          <a
            href={href}
            target="_blank"
            rel="noreferrer"
            className="mt-4 inline-flex w-full items-center justify-center rounded-xl bg-orange-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-orange-700"
          >
            Открыть @{botUsername}
          </a>
        ) : (
          <p className="mt-4 text-sm text-amber-800 dark:text-amber-200">
            Имя бота не настроено на сервере. Обратитесь к администратору.
          </p>
        )}
        <button
          type="button"
          onClick={onClose}
          className="mt-3 w-full rounded-xl border border-zinc-200 py-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-200 dark:hover:bg-zinc-800"
        >
          Закрыть
        </button>
      </div>
    </div>
  )
}

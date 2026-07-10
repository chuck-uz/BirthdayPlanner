import { Bell, Cake, Gift, ListChecks, Users } from 'lucide-react'

import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function AboutPage() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400">
          <Cake className="size-5" aria-hidden />
          <span className="text-sm font-medium">О проекте</span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white sm:text-4xl">
          Как устроен BirthdayPlanner
        </h1>
        <p className="max-w-2xl text-zinc-600 dark:text-zinc-400">
          Сервис помогает не забыть про дни рождения близких и вместе организовать
          подарок — без паролей, только вход через Telegram.
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="mb-1 flex items-center gap-2 text-orange-600 dark:text-orange-400">
            <ListChecks className="size-5" aria-hidden />
            <CardTitle className="text-lg">Профиль и вишлист</CardTitle>
          </div>
          <CardDescription>Что о вас узнают друзья</CardDescription>
        </CardHeader>
        <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          После входа через Telegram укажите имя и дату рождения — по ним вас увидят
          в группах. В вишлисте можно собрать список подарков: название, описание,
          ссылку на магазин и фото. Его видят все, с кем вы состоите в одной группе, —
          удобно, когда не знаешь, что подарить.
        </p>
      </Card>

      <Card>
        <CardHeader>
          <div className="mb-1 flex items-center gap-2 text-orange-600 dark:text-orange-400">
            <Users className="size-5" aria-hidden />
            <CardTitle className="text-lg">Приватные группы</CardTitle>
          </div>
          <CardDescription>Основной способ организовать поздравление</CardDescription>
        </CardHeader>
        <div className="flex flex-col gap-3 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          <p>
            Создайте свою группу — например, «Семья» или «Друзья» — и пригласите
            в неё людей по ссылке. Тот, кто создал группу, становится её админом и
            может назначить админами других участников.
          </p>
          <p>
            На главной странице дни рождения участников каждой вашей группы
            показываются отдельным блоком — ничего не потеряется среди чужих дат.
          </p>
          <p>
            Заранее до дня рождения бот в Telegram уведомляет админов группы, чтобы
            они успели договориться о подарке. Если у именинника нет других админов
            рядом, за неделю предупреждаются уже все участники группы — так шанс
            что-то организовать не теряется.
          </p>
          <p>
            Ссылку-приглашение можно в любой момент перевыпустить — старая сразу
            перестанет работать, и по ней никто новый не попадёт в группу.
          </p>
        </div>
      </Card>

      <Card>
        <CardHeader>
          <div className="mb-1 flex items-center gap-2 text-orange-600 dark:text-orange-400">
            <Bell className="size-5" aria-hidden />
            <CardTitle className="text-lg">Подписка на любого</CardTitle>
          </div>
          <CardDescription>Альтернативный способ, если группа не нужна</CardDescription>
        </CardHeader>
        <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          Помимо групп, можно просто подписаться на день рождения конкретного
          человека прямо с его профиля — колокольчиком рядом с вишлистом. Ближе к
          дате бот в личке предложит вам создать чат для обсуждения подарка и
          пригласить туда остальных подписчиков; именинник об этом не узнает.
        </p>
      </Card>

      <Card className="border-orange-200/80 bg-orange-50/60 dark:border-orange-900/40 dark:bg-orange-950/20">
        <div className="flex items-start gap-3">
          <Gift className="mt-0.5 size-5 shrink-0 text-orange-600 dark:text-orange-400" aria-hidden />
          <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
            Секрет сюрприза сохраняется: сам именинник никогда не видит ни подписки на
            себя, ни обсуждение подарка — вся координация идёт в Telegram, в стороне
            от него.
          </p>
        </div>
      </Card>
    </div>
  )
}

import { Bell, Cake, Gift, ListChecks, Shield, Users } from 'lucide-react'

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
          <CardDescription>Единственный способ организовать поздравление</CardDescription>
        </CardHeader>
        <div className="flex flex-col gap-3 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          <p>
            Создайте свою группу — например, «Семья» или «Друзья» — и пригласите
            в неё людей по ссылке. Тот, кто создал группу, становится её админом и
            может назначить админами других участников. Ссылку-приглашение можно в
            любой момент перевыпустить — старая сразу перестанет работать.
          </p>
          <p>
            На главной странице дни рождения участников каждой вашей группы
            показываются отдельным блоком — ничего не потеряется среди чужих дат, и
            своего дня рождения вы там не увидите.
          </p>
        </div>
      </Card>

      <Card>
        <CardHeader>
          <div className="mb-1 flex items-center gap-2 text-orange-600 dark:text-orange-400">
            <Bell className="size-5" aria-hidden />
            <CardTitle className="text-lg">Подписка внутри группы</CardTitle>
          </div>
          <CardDescription>Кому именно бот пришлёт приглашение в чат</CardDescription>
        </CardHeader>
        <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          Рядом с именем каждого участника вашей группы — колокольчик: подпишитесь
          на конкретного человека, и когда до его ДР останется настроенное группой
          число дней, именно вы (и другие подписчики) получите готовую ссылку на
          секретный чат. Подписаться можно только на того, с кем сейчас есть общая
          группа.
        </p>
      </Card>

      <Card>
        <CardHeader>
          <div className="mb-1 flex items-center gap-2 text-orange-600 dark:text-orange-400">
            <Shield className="size-5" aria-hidden />
            <CardTitle className="text-lg">Как создаётся секретный чат</CardTitle>
          </div>
          <CardDescription>Telegram не даёт ботам создавать группы — это делает человек</CardDescription>
        </CardHeader>
        <div className="flex flex-col gap-3 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          <p>
            Если у именинника есть хотя бы один подписчик, за настроенное число дней
            бот в личке спрашивает всех админов группы (кроме самого именинника):
            «Создать чат?». Кто первый создаст группу в Telegram и добавит туда
            бота — тот и закрывает это событие, остальным приходит «уже занято».
          </p>
          <p>
            Бот сам достаёт ссылку-приглашение и рассылает её подписчикам именинника
            в этой группе. Если у именинника подписчиков нет — бот админов не
            беспокоит, спрашивать не для кого.
          </p>
          <p>
            Исключение: если именинник — единственный админ группы, спросить больше
            некого, поэтому в тот же срок бот предлагает создать чат всем остальным
            участникам группы — независимо от того, есть ли у именинника подписчики.
          </p>
        </div>
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

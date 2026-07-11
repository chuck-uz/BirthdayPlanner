import { useEffect, useState } from 'react'
import {
  CalendarDays,
  CalendarPlus,
  Gift,
  Link2,
  ListChecks,
  Sparkles,
  UserPlus,
  Users,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import {
  buildGoogleCalendarBirthdayUrl,
  daysUntilLabelRu,
  formatAnnualBirthdayRu,
} from '@/lib/birthdayFormat'
import { membersCountLabel } from '@/types/group'
import type { Group, GroupBirthdayMember, GroupBirthdaySection } from '@/types/group'

function displayName(m: GroupBirthdayMember): string {
  return m.full_name?.trim() || `Участник #${m.user_id}`
}

function BirthdayCard({ member }: { member: GroupBirthdayMember }) {
  const [imgFailed, setImgFailed] = useState(false)
  const name = displayName(member)
  const showAvatar = member.has_avatar && !imgFailed
  const calUrl = buildGoogleCalendarBirthdayUrl(name, member.birth_date)

  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border border-zinc-200/80 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950/80">
      <div className="flex min-h-[140px] gap-4 border-b border-zinc-100 bg-gradient-to-br from-zinc-50 to-orange-50/40 p-4 dark:border-zinc-800 dark:from-zinc-900 dark:to-orange-950/20">
        <div className="relative h-28 w-24 shrink-0 overflow-hidden rounded-xl bg-zinc-200/90 dark:bg-zinc-800">
          {showAvatar ? (
            <img
              src={`/api/users/${member.user_id}/avatar`}
              alt=""
              className="size-full object-cover"
              onError={() => setImgFailed(true)}
            />
          ) : (
            <div className="flex size-full items-center justify-center text-zinc-500 dark:text-zinc-400">
              <Gift className="size-10" aria-hidden />
            </div>
          )}
        </div>
        <div className="flex min-w-0 flex-1 flex-col justify-center gap-1">
          <span className="inline-flex w-fit rounded-full bg-orange-500/15 px-2.5 py-0.5 text-xs font-medium text-orange-800 dark:text-orange-300">
            {daysUntilLabelRu(member.days_until)}
          </span>
          <h3 className="text-lg font-semibold leading-tight text-zinc-900 dark:text-white">{name}</h3>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            {formatAnnualBirthdayRu(member.birth_date)}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 p-3">
        <Link
          to={`/users/${member.user_id}#wishlist`}
          className="inline-flex w-full items-center justify-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-sm font-medium text-zinc-800 transition hover:border-orange-300 hover:bg-orange-50/50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:border-orange-800 dark:hover:bg-orange-950/40"
        >
          <ListChecks className="size-4 shrink-0" aria-hidden />
          Вишлист
        </Link>
        <button
          type="button"
          disabled={!calUrl}
          title="Добавить в Google Календарь"
          onClick={() => {
            if (calUrl) window.open(calUrl, '_blank', 'noopener,noreferrer')
          }}
          className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-sm font-medium text-zinc-800 transition hover:border-blue-300 hover:bg-blue-50/50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:border-blue-800 dark:hover:bg-blue-950/30"
        >
          <CalendarPlus className="size-4 shrink-0 text-blue-600 dark:text-blue-400" aria-hidden />
          Google Календарь
        </button>
      </div>
    </article>
  )
}

const ONBOARDING_STEPS = [
  {
    icon: Users,
    text: 'Создайте группу или вступите по приглашению',
  },
  {
    icon: Gift,
    text: 'Участники укажут дату рождения и вишлист',
  },
  {
    icon: CalendarDays,
    text: 'Мы напомним вовремя и поможем собрать чат в Telegram',
  },
] as const

function NoGroupsState() {
  return (
    <div className="flex flex-col items-center rounded-2xl border border-dashed border-zinc-300/90 bg-white/40 px-6 py-12 text-center dark:border-zinc-700 dark:bg-zinc-950/30">
      <Users className="mb-3 size-10 text-zinc-400 dark:text-zinc-500" aria-hidden />
      <p className="text-base font-medium text-zinc-800 dark:text-zinc-200">Пока нет групп</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-zinc-500 dark:text-zinc-400">
        BirthdayPlanner работает через приватные группы — создайте свою или вступите по
        ссылке-приглашению, и здесь появятся дни рождения участников.
      </p>

      <div className="mt-8 grid w-full max-w-2xl gap-3 sm:grid-cols-3">
        {ONBOARDING_STEPS.map(({ icon: Icon, text }, i) => (
          <div
            key={i}
            className="flex flex-col items-center gap-2 rounded-xl border border-zinc-200/80 bg-white px-4 py-5 text-center dark:border-zinc-800 dark:bg-zinc-900/60"
          >
            <span className="flex size-9 items-center justify-center rounded-full bg-orange-500/15 text-orange-700 dark:text-orange-400">
              <Icon className="size-5" aria-hidden />
            </span>
            <p className="text-sm text-zinc-600 dark:text-zinc-400">{text}</p>
          </div>
        ))}
      </div>

      <Link to="/groups" className="mt-8">
        <Button type="button">Перейти к группам</Button>
      </Link>
      <Link
        to="/about"
        className="mt-3 text-sm font-medium text-zinc-500 underline-offset-2 hover:text-orange-600 hover:underline dark:text-zinc-400 dark:hover:text-orange-400"
      >
        Как это устроено
      </Link>
    </div>
  )
}

function NoBirthdayDataState({ groups }: { groups: Group[] }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-zinc-300/90 bg-white/40 px-6 py-8 text-center dark:border-zinc-700 dark:bg-zinc-950/30">
        <CalendarDays className="size-8 text-zinc-400 dark:text-zinc-500" aria-hidden />
        <p className="text-base font-medium text-zinc-800 dark:text-zinc-200">
          В ваших группах пока не видно дней рождения
        </p>
        <p className="mx-auto max-w-md text-sm text-zinc-500 dark:text-zinc-400">
          Участники ещё не указали дату рождения в профиле — попросите их зайти в профиль и
          заполнить её, тогда карточки появятся здесь.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {groups.map((g) => (
          <Link key={g.id} to={`/groups/${g.id}`}>
            <Card className="h-full transition hover:bg-white/70 dark:hover:bg-black/50">
              <CardHeader>
                <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400">
                  <UserPlus className="size-4 shrink-0" aria-hidden />
                  <CardTitle className="text-base">{g.name}</CardTitle>
                </div>
                <CardDescription>{membersCountLabel(g.member_count)}</CardDescription>
              </CardHeader>
              <p className="flex items-center gap-1.5 text-sm font-medium text-zinc-600 dark:text-zinc-400">
                <Link2 className="size-3.5 shrink-0" aria-hidden />
                Перейти в группу
              </p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}

function GroupSection({ section }: { section: GroupBirthdaySection }) {
  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between gap-2">
        <Link
          to={`/groups/${section.group_id}`}
          className="text-lg font-semibold text-zinc-900 hover:text-orange-600 dark:text-white dark:hover:text-orange-400"
        >
          {section.group_name}
        </Link>
        <span className="text-sm text-zinc-500 dark:text-zinc-400">
          {membersCountLabel(section.members.length)}
        </span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {section.members.map((m) => (
          <BirthdayCard key={m.user_id} member={m} />
        ))}
      </div>
    </section>
  )
}

export function HomePage() {
  const [sections, setSections] = useState<GroupBirthdaySection[] | null>(null)
  const [groups, setGroups] = useState<Group[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const [birthdaysRes, groupsRes] = await Promise.all([
          api.get<GroupBirthdaySection[]>('/api/groups/birthdays/upcoming'),
          api.get<Group[]>('/api/groups'),
        ])
        if (!cancelled) {
          setSections(birthdaysRes.data)
          setGroups(groupsRes.data)
          setError(null)
        }
      } catch {
        if (!cancelled) {
          setSections(null)
          setGroups(null)
          setError('Не удалось загрузить список')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400">
          <Sparkles className="size-5" aria-hidden />
          <span className="text-sm font-medium">Обзор</span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-white sm:text-4xl">
          Дни рождения в ваших группах
        </h1>
      </div>

      {error ? (
        <p className="rounded-2xl border border-red-200/80 bg-red-50/80 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </p>
      ) : null}

      {sections === null && !error ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-64 animate-pulse rounded-2xl border border-zinc-200/60 bg-zinc-100/80 dark:border-zinc-800 dark:bg-zinc-900/50"
            />
          ))}
        </div>
      ) : null}

      {sections !== null && sections.length === 0 && !error ? (
        groups && groups.length > 0 ? (
          <NoBirthdayDataState groups={groups} />
        ) : (
          <NoGroupsState />
        )
      ) : null}

      {sections !== null && sections.length > 0 ? (
        <div className="flex flex-col gap-10">
          {sections.map((section) => (
            <GroupSection key={section.group_id} section={section} />
          ))}
        </div>
      ) : null}
    </div>
  )
}

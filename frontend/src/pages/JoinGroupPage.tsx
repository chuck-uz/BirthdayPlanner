import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { PartyPopper } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { groupErrorMessage } from '@/types/group'
import type { Group } from '@/types/group'

export function JoinGroupPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token')?.trim() ?? ''
  const [status, setStatus] = useState<'joining' | 'error'>(token ? 'joining' : 'error')
  const [error, setError] = useState<string | null>(token ? null : 'Ссылка-приглашение не указана.')
  const attempted = useRef(false)

  useEffect(() => {
    if (!token || attempted.current) return
    attempted.current = true
    ;(async () => {
      try {
        const { data } = await api.post<Group>('/api/groups/join', { invite_token: token })
        navigate(`/groups/${data.id}`, { replace: true })
      } catch (e: unknown) {
        const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
        setError(groupErrorMessage(detail))
        setStatus('error')
      }
    })()
  }, [token, navigate])

  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <Card className="max-w-md text-center">
        <CardHeader>
          <div className="mx-auto mb-2 flex size-12 items-center justify-center rounded-2xl bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-400">
            <PartyPopper className="size-6" aria-hidden />
          </div>
          <CardTitle>{status === 'joining' ? 'Вступаем в группу…' : 'Не удалось вступить'}</CardTitle>
          {status === 'error' ? <CardDescription>{error}</CardDescription> : null}
        </CardHeader>
        {status === 'error' ? (
          <Link to="/groups">
            <Button type="button" className="mt-2">
              К моим группам
            </Button>
          </Link>
        ) : null}
      </Card>
    </div>
  )
}

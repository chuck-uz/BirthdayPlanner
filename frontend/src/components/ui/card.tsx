import type { HTMLAttributes, ReactNode } from 'react'

type CardProps = {
  children: ReactNode
  className?: string
} & HTMLAttributes<HTMLDivElement>

export function Card({ children, className = '', ...props }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-white/40 bg-white/55 p-6 shadow-[var(--shadow-glass)] backdrop-blur-xl ring-1 ring-black/5 transition dark:border-white/10 dark:bg-black/40 dark:shadow-[0_24px_64px_rgba(0,0,0,0.55)] dark:ring-white/10 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div className={`mb-4 flex flex-col gap-1 ${className}`}>{children}</div>
  )
}

export function CardTitle({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <h3
      className={`text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-50 ${className}`}
    >
      {children}
    </h3>
  )
}

export function CardDescription({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <p className={`text-sm text-zinc-500 dark:text-zinc-400 ${className}`}>
      {children}
    </p>
  )
}

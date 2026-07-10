import type { HTMLAttributes, ReactNode } from 'react'

type CardProps = {
  children: ReactNode
  className?: string
} & HTMLAttributes<HTMLDivElement>

export function Card({ children, className = '', ...props }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition dark:border-zinc-800 dark:bg-zinc-900 ${className}`}
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

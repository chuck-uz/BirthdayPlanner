import type { ButtonHTMLAttributes, ReactNode } from 'react'

const variants = {
  primary:
    'bg-orange-600 text-white shadow-lg shadow-orange-500/30 hover:bg-orange-500 dark:bg-orange-500 dark:hover:bg-orange-400',
  ghost:
    'bg-transparent text-zinc-800 hover:bg-zinc-100 dark:text-zinc-100 dark:hover:bg-zinc-800',
  outline:
    'bg-transparent text-zinc-800 ring-1 ring-zinc-300/80 hover:bg-zinc-100/80 dark:text-zinc-100 dark:ring-zinc-700 dark:hover:bg-zinc-900/60',
} as const

type Variant = keyof typeof variants

type ButtonProps = {
  children: ReactNode
  className?: string
  variant?: Variant
} & ButtonHTMLAttributes<HTMLButtonElement>

export function Button({
  children,
  className = '',
  variant = 'primary',
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-500 disabled:pointer-events-none disabled:opacity-50 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

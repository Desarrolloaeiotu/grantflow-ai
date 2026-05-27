import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Nacional Colombia | GrantFlow AI',
  description: 'Centro de control para prospección de oportunidades nacionales colombianas',
}

export default function NacionalLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}

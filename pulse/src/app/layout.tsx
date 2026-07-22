import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DS Dashboard',
  description: 'AI autonomous e-commerce dashboard — Shopify + LLM agents',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}

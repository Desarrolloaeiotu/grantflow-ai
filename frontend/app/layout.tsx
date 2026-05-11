import type { Metadata } from 'next'
import './globals.css'
import Sidebar from './components/Sidebar'

export const metadata: Metadata = {
  title: 'GrantFlow AI — aeioTU',
  description: 'Sistema de inteligencia comercial para prospección de grants',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <Sidebar />
        <div className="main">
          {children}
        </div>
      </body>
    </html>
  )
}

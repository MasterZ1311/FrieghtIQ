import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Sidebar from '@/components/layout/Sidebar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'FreightIQ — AI Freight Intelligence | SIH26006',
    template: '%s | FreightIQ',
  },
  description:
    'AI-powered bulk freight procurement intelligence for SAIL. HMM market regimes, Black-Scholes real options, AIS port congestion, tidal scheduling — Thoothukudi & Chennai centric. Smart India Hackathon 2026.',
  keywords: [
    'freight', 'shipping', 'SAIL', 'bulk carrier', 'Thoothukudi', 'VOCPA',
    'Chennai', 'Kamarajar', 'SIH 2026', 'AI logistics', 'freight forecasting',
    'Black-Scholes', 'HMM regime', 'AIS congestion', 'tidal window',
  ],
  openGraph: {
    title: 'FreightIQ — AI Freight Intelligence | SIH26006',
    description: 'Smart India Hackathon 2026 · Problem SIH26006 · Bulk carrier procurement AI for SAIL',
    type: 'website',
    siteName: 'FreightIQ',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-gray-950 text-gray-100 min-h-screen`}>
        <Sidebar />
        <main className="ml-0 lg:ml-64 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  )
}

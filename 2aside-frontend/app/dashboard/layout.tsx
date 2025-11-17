'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { Sidebar } from '@/components/dashboard/sidebar'
import { CurrencySwitcher } from '@/components/dashboard/currency-switcher'
import { useAuthStore, useWalletStore } from '@/lib/store'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const { isAuthenticated } = useAuthStore()
  const { nairaWallet, usdtWallet, selectedCurrency, fetchWallets } = useWalletStore()
  const [isCheckingSetup, setIsCheckingSetup] = useState(true)

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!isAuthenticated) {
      router.push('/login')
      return
    }

    // Fetch wallet data on mount
    const loadWallets = async () => {
      await fetchWallets()
      setIsCheckingSetup(false)
    }

    loadWallets()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated])

  // NOTE: Removed forced redirect to setup page
  // Payment details are now optional until user tries to withdraw
  // Users can browse dashboard without being forced to set up payment methods

  if (!isAuthenticated || isCheckingSetup) {
    return null
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
          <h2 className="text-xl font-semibold text-gray-900">
            Welcome to 2-Aside
          </h2>
          <CurrencySwitcher />
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

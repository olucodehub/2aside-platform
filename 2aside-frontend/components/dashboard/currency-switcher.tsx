'use client'

import { Button } from '@/components/ui/button'
import { useWalletStore } from '@/lib/store'
import { cn } from '@/lib/utils'

export function CurrencySwitcher() {
  const { selectedCurrency, setSelectedCurrency } = useWalletStore()

  return (
    <div className="flex items-center gap-1 rounded-lg bg-gray-100 p-1">
      <Button
        variant="ghost"
        size="sm"
        className={cn(
          'rounded-md px-4 py-1.5',
          selectedCurrency === 'NAIRA'
            ? 'bg-white text-emerald-700 shadow-sm hover:bg-white'
            : 'text-gray-600 hover:text-gray-900'
        )}
        onClick={() => setSelectedCurrency('NAIRA')}
      >
        NAIRA (₦)
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className={cn(
          'rounded-md px-4 py-1.5',
          selectedCurrency === 'USDT'
            ? 'bg-white text-emerald-700 shadow-sm hover:bg-white'
            : 'text-gray-600 hover:text-gray-900'
        )}
        onClick={() => setSelectedCurrency('USDT')}
      >
        USDT ($)
      </Button>
    </div>
  )
}

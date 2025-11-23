'use client'

import { AlertCircle, Mail } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { useWalletStore } from '@/lib/store'

export default function AccountBlockedBanner() {
  const { getCurrentWallet } = useWalletStore()
  const currentWallet = getCurrentWallet()

  // Don't show banner if wallet is not blocked
  if (!currentWallet || !currentWallet.is_blocked) {
    return null
  }

  return (
    <Card className="border-red-300 bg-red-50 shadow-lg">
      <CardContent className="py-4 px-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100">
              <AlertCircle className="h-6 w-6 text-red-600" />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-red-900 mb-2">
              Account Blocked - Action Required
            </h3>
            <div className="space-y-2">
              <p className="text-sm text-red-800 font-medium">
                Your {currentWallet.currency} wallet has been blocked.
              </p>
              {currentWallet.block_reason && (
                <p className="text-sm text-red-700 bg-red-100 p-3 rounded-md border border-red-200">
                  <strong>Reason:</strong> {currentWallet.block_reason}
                </p>
              )}
              <div className="flex items-start gap-2 pt-2">
                <Mail className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-red-800">
                  <strong>How to Resolve:</strong>
                  <p className="mt-1">
                    Please contact our support team at{' '}
                    <a
                      href="mailto:support@2aside.com"
                      className="font-semibold underline hover:text-red-900"
                    >
                      support@2aside.com
                    </a>
                    {' '}to resolve this issue and unblock your account.
                  </p>
                </div>
              </div>
              <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-sm text-yellow-900">
                  <strong>Important:</strong> While your account is blocked, you cannot create
                  new funding or withdrawal requests, or upload payment proofs. All action buttons
                  will be disabled until this issue is resolved.
                </p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

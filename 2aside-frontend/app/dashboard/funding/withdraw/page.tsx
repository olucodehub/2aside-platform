'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowUpRight, Clock, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { fundingService, walletService, handleApiError, MergeCycleInfo } from '@/lib/api'
import { useWalletStore } from '@/lib/store'
import { formatCurrency } from '@/lib/utils'

const NAIRA_PRESETS = [2000, 5000, 10000, 50000, 100000, 300000, 500000]
const USDT_PRESETS = [10, 20, 50, 100, 200, 500, 1000]

function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

export default function WithdrawPage() {
  const router = useRouter()
  const { selectedCurrency, getCurrentWallet } = useWalletStore()
  const [amount, setAmount] = useState('')
  const [balance, setBalance] = useState(0)
  const [loading, setLoading] = useState(false)
  const [loadingBalance, setLoadingBalance] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [mergeCycle, setMergeCycle] = useState<MergeCycleInfo | null>(null)
  const [timeRemaining, setTimeRemaining] = useState<number>(0)

  const currentWallet = getCurrentWallet()
  const isBlocked = currentWallet?.is_blocked || false

  const presets = selectedCurrency === 'NAIRA' ? NAIRA_PRESETS : USDT_PRESETS

  useEffect(() => {
    fetchBalance()
  }, [selectedCurrency])

  useEffect(() => {
    fetchMergeCycleInfo()
    const interval = setInterval(fetchMergeCycleInfo, 60000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (mergeCycle?.time_until_merge_seconds) {
      setTimeRemaining(mergeCycle.time_until_merge_seconds)
      const interval = setInterval(() => {
        setTimeRemaining(prev => Math.max(0, prev - 1))
      }, 1000)
      return () => clearInterval(interval)
    }
  }, [mergeCycle])

  const fetchMergeCycleInfo = async () => {
    try {
      const response = await fundingService.getNextMergeCycle()
      setMergeCycle(response.data.data)
    } catch (err) {
      console.error('Error fetching merge cycle:', err)
    }
  }

  const fetchBalance = async () => {
    try {
      setLoadingBalance(true)
      const response = await walletService.getBalance(selectedCurrency)
      setBalance(response.data.balance)
    } catch (err) {
      console.error('Error fetching balance:', handleApiError(err))
    } finally {
      setLoadingBalance(false)
    }
  }

  const handlePresetClick = (preset: number) => {
    if (preset <= balance) {
      setAmount(preset.toString())
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    const amountNum = parseFloat(amount)

    // Validation
    if (!amountNum || amountNum <= 0) {
      setError('Please enter a valid amount')
      return
    }

    if (amountNum < 1000) {
      setError('Minimum withdrawal amount is ' + formatCurrency(1000, selectedCurrency))
      return
    }

    if (amountNum > balance) {
      setError('Insufficient balance')
      return
    }

    setLoading(true)

    try {
      await fundingService.createWithdrawalRequest(amountNum, selectedCurrency)
      setSuccess(true)

      // Redirect to funding status page after 2 seconds
      setTimeout(() => {
        router.push('/dashboard/funding/status')
      }, 2000)
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
              <ArrowUpRight className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">
              Withdrawal Request Created!
            </h3>
            <p className="mt-2 text-sm text-gray-600">
              Your request for {formatCurrency(parseFloat(amount), selectedCurrency)} has been submitted.
              Redirecting to status page...
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Withdraw Funds</h1>
        <p className="mt-2 text-gray-600">
          Request to withdraw from your {selectedCurrency} wallet
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Available Balance</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingBalance ? (
            <div className="h-8 w-32 animate-pulse rounded bg-gray-200"></div>
          ) : (
            <div className="text-3xl font-bold text-gray-900">
              {formatCurrency(balance, selectedCurrency)}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Merge Cycle Info */}
      {mergeCycle?.has_cycle && (
        <Card className={mergeCycle.can_create_request ? "border-blue-200 bg-blue-50" : "border-orange-200 bg-orange-50"}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Next Merge Cycle
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">Merge Time:</span>
                <span className="text-lg font-bold text-gray-900">
                  {mergeCycle.merge_time ? new Date(mergeCycle.merge_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">Time Until Merge:</span>
                <span className="text-lg font-bold text-blue-600">
                  {formatTime(timeRemaining)}
                </span>
              </div>
              {!mergeCycle.can_create_request && (
                <div className="flex items-start gap-2 p-3 rounded-md bg-orange-100">
                  <AlertCircle className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-orange-800">
                    <strong>Too late!</strong> Requests must be made at least 1 hour before merge.
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>How Batch Matching Works</CardTitle>
          <CardDescription>
            3 merge cycles daily: 9 AM, 3 PM, 9 PM
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-2 text-sm text-gray-600">
            <li>Select the amount you want to withdraw</li>
            <li>Your request waits until the next scheduled merge cycle</li>
            <li>System matches you with users funding (amounts can be split)</li>
            <li>Receive payment from each matched partner</li>
            <li>Confirm receipt for each payment</li>
            <li>Funds are deducted from your wallet once confirmed</li>
          </ol>
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Select Amount</CardTitle>
            <CardDescription>
              Choose from preset amounts below
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
                {error}
              </div>
            )}

            {/* Preset Amounts */}
            <div>
              <Label>Quick Select</Label>
              <div className="mt-2 grid grid-cols-4 gap-2">
                {presets.map((preset) => (
                  <Button
                    key={preset}
                    type="button"
                    variant={amount === preset.toString() ? 'default' : 'outline'}
                    onClick={() => handlePresetClick(preset)}
                    disabled={loading || preset > balance || isBlocked}
                  >
                    {formatCurrency(preset, selectedCurrency)}
                  </Button>
                ))}
              </div>
            </div>

            {/* Selected Amount Display */}
            {!amount && (
              <div className="text-center py-4">
                <p className="text-sm text-gray-500">
                  Please select an amount above
                </p>
              </div>
            )}

            {/* Summary */}
            {amount && (
              <div className="rounded-lg bg-gray-50 p-4">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    Amount to Withdraw
                  </span>
                  <span className="text-lg font-bold text-gray-900">
                    {formatCurrency(parseFloat(amount), selectedCurrency)}
                  </span>
                </div>
                <div className="mt-2 flex justify-between">
                  <span className="text-sm text-gray-600">
                    Remaining Balance
                  </span>
                  <span className="text-sm font-medium text-gray-700">
                    {formatCurrency(balance - parseFloat(amount), selectedCurrency)}
                  </span>
                </div>
              </div>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={loading || !amount || parseFloat(amount) > balance || (mergeCycle && !mergeCycle.can_create_request) || isBlocked}
            >
              {loading ? 'Creating Request...' :
               isBlocked ? 'Account Blocked - Contact Support' :
               (mergeCycle && !mergeCycle.can_create_request) ? 'Cutoff Passed - Wait for Next Cycle' :
               'Create Withdrawal Request'}
            </Button>
          </CardContent>
        </Card>
      </form>

      <Card className="border-yellow-200 bg-yellow-50">
        <CardContent className="pt-6">
          <p className="text-sm text-yellow-900">
            <strong>Important:</strong> Make sure your bank details are up to date before
            withdrawing. Your matched partner will send payment to the account on file.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

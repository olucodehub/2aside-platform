'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowDownRight, Clock, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { fundingService, handleApiError, MergeCycleInfo } from '@/lib/api'
import { useWalletStore } from '@/lib/store'
import { formatCurrency, formatTimeWAT } from '@/lib/utils'

const NAIRA_PRESETS = [2000, 5000, 10000, 50000, 100000, 300000, 500000, 1000000]
const USDT_PRESETS = [10, 20, 50, 100, 200, 500, 1000]

function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

export default function FundingRequestPage() {
  const router = useRouter()
  const { selectedCurrency } = useWalletStore()
  const [amount, setAmount] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [mergeCycle, setMergeCycle] = useState<MergeCycleInfo | null>(null)
  const [timeRemaining, setTimeRemaining] = useState<number>(0)

  const presets = selectedCurrency === 'NAIRA' ? NAIRA_PRESETS : USDT_PRESETS

  useEffect(() => {
    // Only fetch once when component mounts - no automatic refresh
    // User can refresh browser if they want updated info
    fetchMergeCycleInfo()
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

  const handlePresetClick = (preset: number) => {
    setAmount(preset.toString())
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
      setError('Minimum funding amount is ' + formatCurrency(1000, selectedCurrency))
      return
    }

    setLoading(true)

    try {
      await fundingService.createFundingRequest(amountNum, selectedCurrency)
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
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
              <ArrowDownRight className="h-6 w-6 text-emerald-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">
              Funding Request Created!
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
      {/* Header with View Requests Button */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Fund Wallet</h1>
          <p className="mt-2 text-gray-600">
            Request to fund your {selectedCurrency} wallet via P2P matching
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => router.push('/dashboard/funding/status')}
          className="whitespace-nowrap flex-shrink-0"
        >
          View My Requests
        </Button>
      </div>

      {/* Quick Navigation Card */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="py-3 px-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-blue-900">
              Want to check your existing funding or withdrawal requests?
            </p>
            <Button
              variant="link"
              onClick={() => router.push('/dashboard/funding/status')}
              className="text-blue-700 hover:text-blue-900 font-semibold"
            >
              View Status →
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Merge Cycle Info */}
      {mergeCycle?.has_cycle && (
        <Card className={mergeCycle.can_create_request ? "border-emerald-200 bg-emerald-50" : "border-orange-200 bg-orange-50"}>
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
                  {mergeCycle.merge_time ? formatTimeWAT(mergeCycle.merge_time) : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">Time Until Merge:</span>
                <span className="text-lg font-bold text-emerald-600">
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
            <li>Select the amount you want to fund</li>
            <li>Your request waits until the next scheduled merge cycle</li>
            <li>System matches you with users withdrawing (amounts can be split)</li>
            <li>Send payment to each matched partner</li>
            <li>Upload proof of payment for each match</li>
            <li>Once confirmed, funds are credited instantly</li>
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
              <div className="rounded-md bg-red-50 p-3">
                <p className="text-sm text-red-800">{error}</p>
                {error.toLowerCase().includes('pending') && (
                  <Button
                    type="button"
                    variant="link"
                    className="mt-2 text-red-800 hover:text-red-900 p-0 h-auto font-semibold"
                    onClick={() => router.push('/dashboard/funding/status')}
                  >
                    View my pending request →
                  </Button>
                )}
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
                    disabled={loading}
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
                    Amount to Fund
                  </span>
                  <span className="text-lg font-bold text-gray-900">
                    {formatCurrency(parseFloat(amount), selectedCurrency)}
                  </span>
                </div>
              </div>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={loading || !amount || (mergeCycle && !mergeCycle.can_create_request)}
            >
              {loading ? 'Creating Request...' :
               (mergeCycle && !mergeCycle.can_create_request) ? 'Cutoff Passed - Wait for Next Cycle' :
               'Create Funding Request'}
            </Button>
          </CardContent>
        </Card>
      </form>

      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <p className="text-sm text-blue-900">
            <strong>Note:</strong> Once matched, you'll have a limited time to complete
            the payment. Make sure you're ready to send payment before creating a request.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

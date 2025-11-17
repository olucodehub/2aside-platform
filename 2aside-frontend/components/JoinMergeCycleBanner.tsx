'use client'

import { useState, useEffect } from 'react'
import { Clock, Users, AlertCircle, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { fundingService, handleApiError } from '@/lib/api'

export default function JoinMergeCycleBanner() {
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [joining, setJoining] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [timeRemaining, setTimeRemaining] = useState(0)

  // Fetch merge cycle status
  const fetchStatus = async () => {
    try {
      const response = await fundingService.getMergeCycleStatus()
      const data = response.data.data
      setStatus(data)
      setTimeRemaining(data.time_remaining_seconds || 0)
      setLoading(false)
    } catch (err) {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    // Poll every 10 seconds
    const interval = setInterval(fetchStatus, 10000)
    return () => clearInterval(interval)
  }, [])

  // Countdown timer
  useEffect(() => {
    if (timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining((prev) => Math.max(0, prev - 1))
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [timeRemaining])

  const handleJoin = async () => {
    setJoining(true)
    setError('')
    setSuccess('')

    try {
      const response = await fundingService.joinMergeCycle()
      setSuccess(response.data.message)
      // Refresh status
      await fetchStatus()
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setJoining(false)
    }
  }

  // Format time remaining
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Don't show banner if:
  // - Loading
  // - No pending request
  // - Join window not open
  // - Already opted in
  if (loading || !status || !status.has_pending_request || !status.join_window_open || status.already_opted_in) {
    return null
  }

  // Show success state if already joined
  if (status.already_opted_in) {
    return (
      <Card className="border-green-200 bg-green-50 p-4 mb-6">
        <div className="flex items-center gap-3">
          <CheckCircle2 className="h-6 w-6 text-green-600" />
          <div className="flex-1">
            <h3 className="font-semibold text-green-900">You've Joined the Merge Cycle!</h3>
            <p className="text-sm text-green-700">
              Matching will begin after the 5-minute window closes. Check "Active Matches" to see who you're paired with.
            </p>
          </div>
        </div>
      </Card>
    )
  }

  // Show expired state if window closed
  if (status.join_window_expired) {
    return (
      <Card className="border-yellow-200 bg-yellow-50 p-4 mb-6">
        <div className="flex items-center gap-3">
          <AlertCircle className="h-6 w-6 text-yellow-600" />
          <div className="flex-1">
            <h3 className="font-semibold text-yellow-900">Join Window Closed</h3>
            <p className="text-sm text-yellow-700">
              The 5-minute join window has expired. Matching is now in progress.
              Check "Active Matches" to see if you were paired, or wait for the next cycle.
            </p>
          </div>
        </div>
      </Card>
    )
  }

  // Show join prompt
  return (
    <Card className="border-emerald-200 bg-gradient-to-r from-emerald-50 to-blue-50 p-6 mb-6">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
            <Users className="h-6 w-6 text-emerald-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900">Merge Cycle Window is Open!</h3>
            <p className="text-sm text-gray-600 mt-1">
              You have a pending <span className="font-semibold text-emerald-600">{status.request_type}</span> request.
              Join now to be matched with other users.
            </p>
          </div>
          <div className="flex-shrink-0 text-right">
            <div className="flex items-center gap-2 text-emerald-600">
              <Clock className="h-5 w-5" />
              <span className="text-2xl font-bold font-mono">
                {formatTime(timeRemaining)}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">Time remaining</p>
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-800 border border-red-200">
            {error}
          </div>
        )}
        {success && (
          <div className="rounded-md bg-green-50 p-3 text-sm text-green-800 border border-green-200">
            {success}
          </div>
        )}

        {/* Info boxes */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="bg-white bg-opacity-60 rounded-lg p-3 border border-emerald-100">
            <p className="text-xs font-semibold text-gray-600 uppercase mb-1">How It Works</p>
            <p className="text-sm text-gray-700">
              Click "Join Now" within 5 minutes. After the window closes, the system automatically matches all participants.
            </p>
          </div>
          <div className="bg-white bg-opacity-60 rounded-lg p-3 border border-blue-100">
            <p className="text-xs font-semibold text-gray-600 uppercase mb-1">What Happens Next</p>
            <p className="text-sm text-gray-700">
              You'll see who you're matched with in "Active Matches". Then complete the payment/confirmation process.
            </p>
          </div>
        </div>

        {/* Action button */}
        <Button
          onClick={handleJoin}
          disabled={joining || !status.can_join}
          className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-6 text-lg"
          size="lg"
        >
          {joining ? 'Joining...' : 'Join Merge Cycle Now'}
        </Button>

        {/* Warning */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-xs text-blue-800">
            <strong className="font-semibold">Important:</strong> If you don't join within 5 minutes,
            you won't be matched this cycle and will need to wait for the next one (9am, 3pm, or 9pm).
          </p>
        </div>
      </div>
    </Card>
  )
}

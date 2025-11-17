'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Clock, User, Phone, Building2, Wallet, Upload, CheckCircle,
  AlertCircle, Timer, RefreshCcw, Copy, Check
} from 'lucide-react'
import { fundingService, handleApiError } from '@/lib/api'
import { useWalletStore } from '@/lib/store'

interface MatchPair {
  pair_id: string
  role: 'funder' | 'withdrawer'
  amount: string
  currency: string
  matched_user: {
    username: string
    phone: string
    payment_details?: any
  }
  proof_uploaded: boolean
  proof_url?: string
  proof_confirmed?: boolean
  proof_deadline?: string
  confirmation_deadline?: string
  time_remaining_seconds?: number
  can_extend?: boolean
  extension_requested?: boolean
  awaiting_proof?: boolean
  awaiting_confirmation?: boolean
  created_at: string
}

export default function ActiveMatchesPage() {
  const { selectedCurrency } = useWalletStore()
  const [matches, setMatches] = useState<{ as_funder: MatchPair[]; as_withdrawer: MatchPair[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [proofUrl, setProofUrl] = useState<{ [key: string]: string }>({})
  const [uploading, setUploading] = useState<{ [key: string]: boolean }>({})
  const [confirming, setConfirming] = useState<{ [key: string]: boolean }>({})
  const [extending, setExtending] = useState<{ [key: string]: boolean }>({})
  const [copiedPhone, setCopiedPhone] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const fetchMatches = async () => {
    try {
      const response = await fundingService.getMyActiveMatches()
      setMatches(response.data.data)
      setLoading(false)
      setRefreshing(false)
    } catch (err) {
      setError(handleApiError(err))
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchMatches()
    // Poll every 30 seconds
    const interval = setInterval(fetchMatches, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchMatches()
  }

  const handleUploadProof = async (pairId: string) => {
    if (!proofUrl[pairId]?.trim()) {
      setError('Please enter a proof URL')
      return
    }

    setUploading({ ...uploading, [pairId]: true })
    setError('')
    setSuccess('')

    try {
      await fundingService.uploadProof(pairId, proofUrl[pairId])
      setSuccess('Proof uploaded successfully! Waiting for receiver confirmation...')
      await fetchMatches()
      setProofUrl({ ...proofUrl, [pairId]: '' })
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setUploading({ ...uploading, [pairId]: false })
    }
  }

  const handleConfirmProof = async (pairId: string) => {
    setConfirming({ ...confirming, [pairId]: true })
    setError('')
    setSuccess('')

    try {
      await fundingService.confirmProof(pairId)
      setSuccess('Payment confirmed! Your wallet balance has been updated.')
      await fetchMatches()
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setConfirming({ ...confirming, [pairId]: false })
    }
  }

  const handleRequestExtension = async (pairId: string) => {
    setExtending({ ...extending, [pairId]: true })
    setError('')
    setSuccess('')

    try {
      const response = await fundingService.requestExtension(pairId)
      setSuccess(response.data.message)
      await fetchMatches()
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setExtending({ ...extending, [pairId]: false })
    }
  }

  const copyToClipboard = (text: string, type: string) => {
    navigator.clipboard.writeText(text)
    setCopiedPhone(type)
    setTimeout(() => setCopiedPhone(null), 2000)
  }

  const formatTime = (seconds?: number) => {
    if (!seconds) return 'N/A'
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours}h ${mins}m ${secs}s`
  }

  const formatCurrency = (amount: string, currency: string) => {
    const num = parseFloat(amount)
    if (currency === 'NAIRA') {
      return `₦${num.toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    }
    return `${num.toFixed(2)} USDT`
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Active Matches</h1>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
          <p className="text-gray-500 mt-4">Loading matches...</p>
        </div>
      </div>
    )
  }

  const totalMatches = (matches?.as_funder.length || 0) + (matches?.as_withdrawer.length || 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Active Matches</h1>
          <p className="text-gray-600 mt-1">
            View and manage your matched funding/withdrawal pairs
          </p>
        </div>
        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2"
        >
          <RefreshCcw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Messages */}
      {error && (
        <div className="rounded-md bg-red-50 p-4 text-sm text-red-800 border border-red-200">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            {error}
          </div>
        </div>
      )}
      {success && (
        <div className="rounded-md bg-green-50 p-4 text-sm text-green-800 border border-green-200">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5" />
            {success}
          </div>
        </div>
      )}

      {/* No matches */}
      {totalMatches === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <Users className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Active Matches</h3>
            <p className="text-gray-600">
              You don't have any active matches at the moment. Create a funding or withdrawal request
              and join the next merge cycle to get matched.
            </p>
          </CardContent>
        </Card>
      )}

      {/* As Funder (You need to pay) */}
      {matches && matches.as_funder.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Upload className="h-5 w-5 text-emerald-600" />
            You Need to Pay ({matches.as_funder.length})
          </h2>

          {matches.as_funder.map((match) => (
            <Card key={match.pair_id} className="border-emerald-200">
              <CardHeader className="bg-emerald-50">
                <CardTitle className="text-lg flex items-center justify-between">
                  <span>Pay {formatCurrency(match.amount, match.currency)}</span>
                  {match.time_remaining_seconds && match.time_remaining_seconds > 0 && (
                    <div className="flex items-center gap-2 text-orange-600">
                      <Timer className="h-5 w-5" />
                      <span className="font-mono">{formatTime(match.time_remaining_seconds)}</span>
                    </div>
                  )}
                </CardTitle>
                <CardDescription>Role: Funder • Send payment to the person below</CardDescription>
              </CardHeader>
              <CardContent className="pt-6 space-y-4">
                {/* Matched User Info */}
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <h4 className="font-semibold text-gray-900">Send Payment To:</h4>

                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium">{match.matched_user.username}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-mono">{match.matched_user.phone}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(match.matched_user.phone, `phone-${match.pair_id}`)}
                      className="ml-auto"
                    >
                      {copiedPhone === `phone-${match.pair_id}` ? (
                        <Check className="h-4 w-4 text-green-600" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>

                  {/* Payment Details */}
                  {match.matched_user.payment_details && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      {match.matched_user.payment_details.type === 'bank' ? (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-emerald-700 font-semibold">
                            <Building2 className="h-5 w-5" />
                            Bank Account Details
                          </div>
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            <div>
                              <p className="text-gray-600">Account Number</p>
                              <p className="font-mono font-semibold">{match.matched_user.payment_details.account_number}</p>
                            </div>
                            <div>
                              <p className="text-gray-600">Account Name</p>
                              <p className="font-semibold">{match.matched_user.payment_details.account_name}</p>
                            </div>
                            <div className="col-span-2">
                              <p className="text-gray-600">Bank Name</p>
                              <p className="font-semibold">{match.matched_user.payment_details.bank_name}</p>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-emerald-700 font-semibold">
                            <Wallet className="h-5 w-5" />
                            USDT Wallet Address (BEP20)
                          </div>
                          <p className="font-mono text-sm break-all bg-white p-3 rounded border">
                            {match.matched_user.payment_details.wallet_address}
                          </p>
                          <p className="text-xs text-gray-500">Network: BEP20 (Binance Smart Chain)</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Upload Proof Section */}
                {!match.proof_uploaded ? (
                  <div className="space-y-3">
                    <Label htmlFor={`proof-${match.pair_id}`}>Upload Payment Proof (Image URL)</Label>
                    <div className="flex gap-2">
                      <Input
                        id={`proof-${match.pair_id}`}
                        placeholder="https://example.com/receipt.jpg"
                        value={proofUrl[match.pair_id] || ''}
                        onChange={(e) => setProofUrl({ ...proofUrl, [match.pair_id]: e.target.value })}
                        disabled={uploading[match.pair_id]}
                      />
                      <Button
                        onClick={() => handleUploadProof(match.pair_id)}
                        disabled={uploading[match.pair_id]}
                      >
                        {uploading[match.pair_id] ? 'Uploading...' : 'Upload'}
                      </Button>
                    </div>

                    {/* Extension Button */}
                    {match.can_extend && (
                      <Button
                        variant="outline"
                        onClick={() => handleRequestExtension(match.pair_id)}
                        disabled={extending[match.pair_id]}
                        className="w-full"
                      >
                        <Clock className="h-4 w-4 mr-2" />
                        {extending[match.pair_id] ? 'Requesting...' : 'Request 1-Hour Extension'}
                      </Button>
                    )}
                    {match.extension_requested && (
                      <p className="text-sm text-green-600 flex items-center gap-2">
                        <CheckCircle className="h-4 w-4" />
                        Extension granted! You have 1 extra hour.
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-green-700 mb-2">
                      <CheckCircle className="h-5 w-5" />
                      <span className="font-semibold">Proof Uploaded</span>
                    </div>
                    <p className="text-sm text-green-700">
                      Waiting for {match.matched_user.username} to confirm receipt...
                    </p>
                    {match.proof_url && (
                      <a
                        href={match.proof_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:underline mt-2 block"
                      >
                        View Proof
                      </a>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* As Withdrawer (You need to confirm) */}
      {matches && matches.as_withdrawer.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-blue-600" />
            You Need to Confirm ({matches.as_withdrawer.length})
          </h2>

          {matches.as_withdrawer.map((match) => (
            <Card key={match.pair_id} className="border-blue-200">
              <CardHeader className="bg-blue-50">
                <CardTitle className="text-lg flex items-center justify-between">
                  <span>Receive {formatCurrency(match.amount, match.currency)}</span>
                  {match.time_remaining_seconds && match.time_remaining_seconds > 0 && (
                    <div className="flex items-center gap-2 text-orange-600">
                      <Timer className="h-5 w-5" />
                      <span className="font-mono">{formatTime(match.time_remaining_seconds)}</span>
                    </div>
                  )}
                </CardTitle>
                <CardDescription>Role: Withdrawer • Confirm payment from the person below</CardDescription>
              </CardHeader>
              <CardContent className="pt-6 space-y-4">
                {/* Matched User Info */}
                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                  <h4 className="font-semibold text-gray-900">Expecting Payment From:</h4>

                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium">{match.matched_user.username}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-mono">{match.matched_user.phone}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(match.matched_user.phone, `phone-w-${match.pair_id}`)}
                      className="ml-auto"
                    >
                      {copiedPhone === `phone-w-${match.pair_id}` ? (
                        <Check className="h-4 w-4 text-green-600" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                {/* Confirmation Section */}
                {match.awaiting_proof ? (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-yellow-700">
                      <Clock className="h-5 w-5" />
                      <span className="font-semibold">Waiting for Payment Proof</span>
                    </div>
                    <p className="text-sm text-yellow-700 mt-2">
                      {match.matched_user.username} has 4 hours to send payment and upload proof.
                    </p>
                  </div>
                ) : match.awaiting_confirmation ? (
                  <div className="space-y-3">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-sm text-blue-700 font-semibold mb-2">Payment Proof Uploaded!</p>
                      {match.proof_url && (
                        <a
                          href={match.proof_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:underline block mb-3"
                        >
                          View Payment Proof
                        </a>
                      )}
                      <p className="text-sm text-blue-700">
                        Please check your account/wallet and confirm if you received the payment.
                      </p>
                    </div>

                    <Button
                      onClick={() => handleConfirmProof(match.pair_id)}
                      disabled={confirming[match.pair_id]}
                      className="w-full bg-green-600 hover:bg-green-700"
                    >
                      {confirming[match.pair_id] ? 'Confirming...' : 'Confirm Payment Received'}
                    </Button>

                    <p className="text-xs text-gray-500 text-center">
                      Only confirm after you've verified the payment in your account
                    </p>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

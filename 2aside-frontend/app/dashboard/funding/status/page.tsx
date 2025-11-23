'use client'

import { useState, useEffect } from 'react'
import { CheckCircle, Clock, Upload, User, Phone, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { fundingService, handleApiError, FundingRequest, WithdrawalRequest } from '@/lib/api'
import { formatCurrency, formatDateWAT } from '@/lib/utils'
import { useWalletStore } from '@/lib/store'

export default function FundingStatusPage() {
  const { selectedCurrency, getCurrentWallet } = useWalletStore()
  const [fundingRequests, setFundingRequests] = useState<FundingRequest[]>([])
  const [withdrawalRequests, setWithdrawalRequests] = useState<WithdrawalRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [uploadingProof, setUploadingProof] = useState<string | null>(null)
  const [proofFile, setProofFile] = useState<{ [key: string]: File | null }>({})
  const [cancelingRequest, setCancelingRequest] = useState<string | null>(null)

  const currentWallet = getCurrentWallet()
  const isBlocked = currentWallet?.is_blocked || false

  useEffect(() => {
    // Only fetch once when component mounts or currency changes
    // No automatic refresh - user can manually refresh browser if needed
    fetchRequests()
  }, [selectedCurrency])

  const fetchRequests = async () => {
    try {
      setLoading(true)
      const [fundingRes, withdrawalRes] = await Promise.all([
        fundingService.getMyFundingRequests(),
        fundingService.getMyWithdrawalRequests()
      ])

      const fundingData = fundingRes.data.data || []
      const withdrawalData = withdrawalRes.data.data || []

      // Filter by currency
      setFundingRequests(fundingData.filter((r: FundingRequest) => r.currency === selectedCurrency))
      setWithdrawalRequests(withdrawalData.filter((r: WithdrawalRequest) => r.currency === selectedCurrency))
    } catch (err) {
      console.error('Error fetching requests:', handleApiError(err))
    } finally {
      setLoading(false)
    }
  }

  const handleUploadProof = async (pairId: string) => {
    const file = proofFile[pairId]
    if (!file) {
      alert('Please select a file to upload')
      return
    }

    try {
      setUploadingProof(pairId)
      await fundingService.uploadProof(pairId, file)
      setProofFile({ ...proofFile, [pairId]: null })
      alert('Proof uploaded successfully!')
      fetchRequests()
    } catch (err) {
      alert(handleApiError(err))
    } finally {
      setUploadingProof(null)
    }
  }

  const handleConfirmProof = async (pairId: string) => {
    if (!confirm('Are you sure you received payment? This cannot be undone.')) {
      return
    }

    try {
      await fundingService.confirmProof(pairId)
      alert('Payment confirmed! Balances updated.')
      fetchRequests()
    } catch (err) {
      alert(handleApiError(err))
    }
  }

  const handleCancelFundingRequest = async (requestId: string) => {
    if (!confirm('Are you sure you want to cancel this funding request? This cannot be undone.')) {
      return
    }

    try {
      setCancelingRequest(requestId)
      await fundingService.cancelFundingRequest(requestId)
      alert('Funding request cancelled successfully!')
      fetchRequests()
    } catch (err) {
      alert(handleApiError(err))
    } finally {
      setCancelingRequest(null)
    }
  }

  const handleCancelWithdrawalRequest = async (requestId: string) => {
    if (!confirm('Are you sure you want to cancel this withdrawal request? This cannot be undone.')) {
      return
    }

    try {
      setCancelingRequest(requestId)
      await fundingService.cancelWithdrawalRequest(requestId)
      alert('Withdrawal request cancelled successfully!')
      fetchRequests()
    } catch (err) {
      alert(handleApiError(err))
    } finally {
      setCancelingRequest(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Loading your requests...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Funding & Withdrawal Status</h1>
        <p className="mt-2 text-gray-600">
          Track your {selectedCurrency} requests and matched users
        </p>
      </div>

      {/* Info Alert */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <div className="flex items-start gap-3">
          <Clock className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-medium text-blue-900">Cancellation Policy</h3>
            <p className="text-sm text-blue-800 mt-1">
              You can cancel unmatched requests up to <strong>10 minutes before</strong> the next merge cycle
              (9 AM, 3 PM, or 9 PM WAT). Once matched or within 10 minutes of merge, requests cannot be cancelled.
            </p>
          </div>
        </div>
      </div>

      {/* Funding Requests */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Funding Requests (Deposits)</h2>
        {fundingRequests.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-gray-500">
              No funding requests yet
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {fundingRequests.map((request) => (
              <Card key={request.id} className={request.is_completed ? "border-green-200 bg-green-50" : ""}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">
                        Funding Request - {formatCurrency(parseFloat(request.amount), selectedCurrency)}
                      </CardTitle>
                      <CardDescription>
                        Requested {formatDateWAT(request.requested_at)}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      {request.is_completed && (
                        <span className="flex items-center gap-1 text-sm font-medium text-green-600">
                          <CheckCircle className="h-4 w-4" />
                          Completed
                        </span>
                      )}
                      {!request.is_fully_matched && !request.is_completed && (
                        <>
                          <span className="flex items-center gap-1 text-sm font-medium text-orange-600">
                            <Clock className="h-4 w-4" />
                            Waiting for Match
                          </span>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleCancelFundingRequest(request.id)}
                            disabled={cancelingRequest === request.id}
                          >
                            <XCircle className="h-4 w-4 mr-1" />
                            {cancelingRequest === request.id ? 'Canceling...' : 'Cancel'}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Total Amount:</span>
                      <p className="font-semibold">{formatCurrency(parseFloat(request.amount), selectedCurrency)}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Remaining:</span>
                      <p className="font-semibold">{formatCurrency(parseFloat(request.amount_remaining), selectedCurrency)}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Status:</span>
                      <p className="font-semibold">
                        {request.is_completed ? 'Completed' :
                         request.is_fully_matched ? 'Matched' :
                         'Pending'}
                      </p>
                    </div>
                  </div>

                  {/* Matched Users */}
                  {request.matched_users && request.matched_users.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Matched With:</h4>
                      <div className="space-y-3">
                        {request.matched_users.map((matchedUser) => (
                          <div key={matchedUser.pair_id} className="border rounded-lg p-4 bg-white">
                            <div className="flex justify-between items-start mb-3">
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <User className="h-4 w-4 text-gray-500" />
                                  <span className="font-medium">{matchedUser.username}</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                  <Phone className="h-3 w-3" />
                                  <span>{matchedUser.phone}</span>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="text-sm text-gray-600">Amount</p>
                                <p className="font-bold text-lg">{formatCurrency(parseFloat(matchedUser.amount), selectedCurrency)}</p>
                              </div>
                            </div>

                            {/* Proof Upload Section */}
                            {!matchedUser.proof_confirmed && (
                              <div className="border-t pt-3 mt-3">
                                {!matchedUser.proof_uploaded ? (
                                  <div className="space-y-2">
                                    <Label htmlFor={`proof-${matchedUser.pair_id}`}>Upload Proof of Payment</Label>
                                    <div className="flex gap-2">
                                      <Input
                                        id={`proof-${matchedUser.pair_id}`}
                                        type="file"
                                        accept="image/*,.pdf"
                                        onChange={(e) => {
                                          const file = e.target.files?.[0] || null
                                          setProofFile({ ...proofFile, [matchedUser.pair_id]: file })
                                        }}
                                        disabled={uploadingProof === matchedUser.pair_id || isBlocked}
                                        className="cursor-pointer"
                                      />
                                      <Button
                                        size="sm"
                                        onClick={() => handleUploadProof(matchedUser.pair_id)}
                                        disabled={uploadingProof === matchedUser.pair_id || !proofFile[matchedUser.pair_id] || isBlocked}
                                        title={isBlocked ? 'Account blocked - Cannot upload proof' : ''}
                                      >
                                        <Upload className="h-4 w-4 mr-1" />
                                        {uploadingProof === matchedUser.pair_id ? 'Uploading...' : 'Upload'}
                                      </Button>
                                    </div>
                                    {proofFile[matchedUser.pair_id] && (
                                      <p className="text-xs text-emerald-600">
                                        Selected: {proofFile[matchedUser.pair_id]?.name}
                                      </p>
                                    )}
                                    <p className="text-xs text-gray-500">
                                      Send {formatCurrency(parseFloat(matchedUser.amount), selectedCurrency)} to {matchedUser.username} and upload payment screenshot
                                    </p>
                                  </div>
                                ) : (
                                  <div className="flex items-center justify-between">
                                    <span className="text-sm text-green-600 flex items-center gap-1">
                                      <CheckCircle className="h-4 w-4" />
                                      Proof uploaded - Waiting for confirmation
                                    </span>
                                  </div>
                                )}
                              </div>
                            )}

                            {matchedUser.proof_confirmed && (
                              <div className="border-t pt-3 mt-3">
                                <span className="text-sm text-green-600 font-medium flex items-center gap-1">
                                  <CheckCircle className="h-4 w-4" />
                                  Payment Confirmed ✓
                                </span>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Withdrawal Requests */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Withdrawal Requests</h2>
        {withdrawalRequests.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-gray-500">
              No withdrawal requests yet
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {withdrawalRequests.map((request) => (
              <Card key={request.id} className={request.is_completed ? "border-green-200 bg-green-50" : ""}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">
                        Withdrawal Request - {formatCurrency(parseFloat(request.amount), selectedCurrency)}
                      </CardTitle>
                      <CardDescription>
                        Requested {formatDateWAT(request.requested_at)}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      {request.is_completed && (
                        <span className="flex items-center gap-1 text-sm font-medium text-green-600">
                          <CheckCircle className="h-4 w-4" />
                          Completed
                        </span>
                      )}
                      {!request.is_fully_matched && !request.is_completed && (
                        <>
                          <span className="flex items-center gap-1 text-sm font-medium text-orange-600">
                            <Clock className="h-4 w-4" />
                            Waiting for Match
                          </span>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleCancelWithdrawalRequest(request.id)}
                            disabled={cancelingRequest === request.id}
                          >
                            <XCircle className="h-4 w-4 mr-1" />
                            {cancelingRequest === request.id ? 'Canceling...' : 'Cancel'}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Total Amount:</span>
                      <p className="font-semibold">{formatCurrency(parseFloat(request.amount), selectedCurrency)}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Remaining:</span>
                      <p className="font-semibold">{formatCurrency(parseFloat(request.amount_remaining), selectedCurrency)}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Status:</span>
                      <p className="font-semibold">
                        {request.is_completed ? 'Completed' :
                         request.is_fully_matched ? 'Matched' :
                         'Pending'}
                      </p>
                    </div>
                  </div>

                  {/* Matched Users */}
                  {request.matched_users && request.matched_users.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Matched With:</h4>
                      <div className="space-y-3">
                        {request.matched_users.map((matchedUser) => (
                          <div key={matchedUser.pair_id} className="border rounded-lg p-4 bg-white">
                            <div className="flex justify-between items-start mb-3">
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <User className="h-4 w-4 text-gray-500" />
                                  <span className="font-medium">{matchedUser.username}</span>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                  <Phone className="h-3 w-3" />
                                  <span>{matchedUser.phone}</span>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="text-sm text-gray-600">Amount</p>
                                <p className="font-bold text-lg">{formatCurrency(parseFloat(matchedUser.amount), selectedCurrency)}</p>
                              </div>
                            </div>

                            {/* Confirmation Section */}
                            {!matchedUser.proof_confirmed && (
                              <div className="border-t pt-3 mt-3">
                                {!matchedUser.proof_uploaded ? (
                                  <p className="text-sm text-gray-600">
                                    Waiting for {matchedUser.username} to upload proof of payment...
                                  </p>
                                ) : (
                                  <div className="space-y-2">
                                    <p className="text-sm text-gray-600">
                                      {matchedUser.username} has uploaded proof. Confirm if you received payment:
                                    </p>
                                    <Button
                                      size="sm"
                                      onClick={() => handleConfirmProof(matchedUser.pair_id)}
                                      className="w-full"
                                      disabled={isBlocked}
                                      title={isBlocked ? 'Account blocked - Cannot confirm receipt' : ''}
                                    >
                                      <CheckCircle className="h-4 w-4 mr-1" />
                                      Confirm Receipt of {formatCurrency(parseFloat(matchedUser.amount), selectedCurrency)}
                                    </Button>
                                  </div>
                                )}
                              </div>
                            )}

                            {matchedUser.proof_confirmed && (
                              <div className="border-t pt-3 mt-3">
                                <span className="text-sm text-green-600 font-medium flex items-center gap-1">
                                  <CheckCircle className="h-4 w-4" />
                                  Payment Confirmed ✓
                                </span>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

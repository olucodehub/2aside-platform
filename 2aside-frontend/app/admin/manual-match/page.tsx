'use client'

import { useState, useEffect } from 'react'
import { Shuffle, Users, Phone, ArrowRight, CheckCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { adminService, handleApiError, UnmatchedRequest } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { useWalletStore } from '@/lib/store'

export default function ManualMatchPage() {
  const { selectedCurrency, setSelectedCurrency } = useWalletStore()
  const [fundingRequests, setFundingRequests] = useState<UnmatchedRequest[]>([])
  const [withdrawalRequests, setWithdrawalRequests] = useState<UnmatchedRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [matching, setMatching] = useState(false)
  const [error, setError] = useState('')

  const [selectedFunding, setSelectedFunding] = useState<string>('')
  const [selectedWithdrawal, setSelectedWithdrawal] = useState<string>('')
  const [matchAmount, setMatchAmount] = useState('')

  useEffect(() => {
    fetchUnmatchedRequests()
  }, [selectedCurrency])

  const fetchUnmatchedRequests = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await adminService.getUnmatchedRequests(selectedCurrency)
      setFundingRequests(response.data.data.funding_requests || [])
      setWithdrawalRequests(response.data.data.withdrawal_requests || [])
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setLoading(false)
    }
  }

  const selectedFundingRequest = fundingRequests.find(r => r.id === selectedFunding)
  const selectedWithdrawalRequest = withdrawalRequests.find(r => r.id === selectedWithdrawal)

  const maxMatchAmount = selectedFundingRequest && selectedWithdrawalRequest
    ? Math.min(
        parseFloat(selectedFundingRequest.amount_remaining),
        parseFloat(selectedWithdrawalRequest.amount_remaining)
      )
    : 0

  const handleMatch = async () => {
    if (!selectedFunding || !selectedWithdrawal || !matchAmount) {
      alert('Please select both requests and enter a match amount')
      return
    }

    const amount = parseFloat(matchAmount)
    if (amount <= 0) {
      alert('Match amount must be greater than 0')
      return
    }

    if (amount > maxMatchAmount) {
      alert(`Match amount cannot exceed ${formatCurrency(maxMatchAmount, selectedCurrency)}`)
      return
    }

    if (!confirm(`Match ${formatCurrency(amount, selectedCurrency)} between ${selectedFundingRequest?.username} and ${selectedWithdrawalRequest?.username}?`)) {
      return
    }

    try {
      setMatching(true)
      await adminService.manualMatch(selectedFunding, selectedWithdrawal, amount)
      alert('Successfully matched!')

      // Reset form
      setSelectedFunding('')
      setSelectedWithdrawal('')
      setMatchAmount('')

      // Refresh data
      fetchUnmatchedRequests()
    } catch (err) {
      alert(handleApiError(err))
    } finally {
      setMatching(false)
    }
  }

  const handleQuickMatch = () => {
    if (maxMatchAmount > 0) {
      setMatchAmount(maxMatchAmount.toString())
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Loading unmatched requests...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Manual Matching</h1>
          <p className="mt-2 text-gray-600">
            Manually match funding and withdrawal requests
          </p>
        </div>
        <div className="flex gap-3">
          <div className="flex gap-2">
            <Button
              variant={selectedCurrency === 'NAIRA' ? 'default' : 'outline'}
              onClick={() => setSelectedCurrency('NAIRA')}
              size="sm"
            >
              NAIRA
            </Button>
            <Button
              variant={selectedCurrency === 'USDT' ? 'default' : 'outline'}
              onClick={() => setSelectedCurrency('USDT')}
              size="sm"
            >
              USDT
            </Button>
          </div>
          <Button onClick={fetchUnmatchedRequests} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      )}

      {fundingRequests.length === 0 && withdrawalRequests.length === 0 && (
        <Card>
          <CardContent className="pt-6 text-center py-12">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              All Matched!
            </h3>
            <p className="text-gray-600">
              There are no unmatched requests for {selectedCurrency} at this time.
            </p>
          </CardContent>
        </Card>
      )}

      {(fundingRequests.length > 0 || withdrawalRequests.length > 0) && (
        <div className="grid grid-cols-2 gap-6">
          {/* Funding Requests Column */}
          <Card className="border-orange-200">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="h-5 w-5 text-orange-600" />
                Funding Requests ({fundingRequests.length})
              </CardTitle>
              <CardDescription>Select a user who wants to deposit</CardDescription>
            </CardHeader>
            <CardContent>
              {fundingRequests.length === 0 ? (
                <p className="text-center text-gray-500 py-8">No funding requests</p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {fundingRequests.map((request) => (
                    <div
                      key={request.id}
                      onClick={() => setSelectedFunding(request.id)}
                      className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                        selectedFunding === request.id
                          ? 'border-orange-500 bg-orange-50'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-1">
                        <div>
                          <p className="font-semibold">{request.username}</p>
                          <div className="flex items-center gap-1 text-xs text-gray-600">
                            <Phone className="h-3 w-3" />
                            <span>{request.phone}</span>
                          </div>
                        </div>
                        {selectedFunding === request.id && (
                          <CheckCircle className="h-5 w-5 text-orange-600" />
                        )}
                      </div>
                      <div className="flex justify-between items-center mt-2 pt-2 border-t text-sm">
                        <span className="text-gray-600">Remaining:</span>
                        <span className="font-bold text-orange-600">
                          {formatCurrency(parseFloat(request.amount_remaining), selectedCurrency)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Withdrawal Requests Column */}
          <Card className="border-blue-200">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="h-5 w-5 text-blue-600" />
                Withdrawal Requests ({withdrawalRequests.length})
              </CardTitle>
              <CardDescription>Select a user who wants to withdraw</CardDescription>
            </CardHeader>
            <CardContent>
              {withdrawalRequests.length === 0 ? (
                <p className="text-center text-gray-500 py-8">No withdrawal requests</p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {withdrawalRequests.map((request) => (
                    <div
                      key={request.id}
                      onClick={() => setSelectedWithdrawal(request.id)}
                      className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                        selectedWithdrawal === request.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-1">
                        <div>
                          <p className="font-semibold">{request.username}</p>
                          <div className="flex items-center gap-1 text-xs text-gray-600">
                            <Phone className="h-3 w-3" />
                            <span>{request.phone}</span>
                          </div>
                        </div>
                        {selectedWithdrawal === request.id && (
                          <CheckCircle className="h-5 w-5 text-blue-600" />
                        )}
                      </div>
                      <div className="flex justify-between items-center mt-2 pt-2 border-t text-sm">
                        <span className="text-gray-600">Remaining:</span>
                        <span className="font-bold text-blue-600">
                          {formatCurrency(parseFloat(request.amount_remaining), selectedCurrency)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Match Form */}
      {selectedFunding && selectedWithdrawal && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shuffle className="h-5 w-5 text-green-600" />
              Create Match
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Match Summary */}
            <div className="grid grid-cols-3 gap-4 items-center">
              <div className="bg-orange-100 rounded-lg p-4">
                <p className="text-xs text-gray-600 mb-1">Funding</p>
                <p className="font-bold text-lg">{selectedFundingRequest?.username}</p>
                <p className="text-sm text-orange-600 mt-1">
                  Available: {formatCurrency(parseFloat(selectedFundingRequest?.amount_remaining || '0'), selectedCurrency)}
                </p>
              </div>

              <div className="text-center">
                <ArrowRight className="h-8 w-8 text-gray-400 mx-auto" />
              </div>

              <div className="bg-blue-100 rounded-lg p-4">
                <p className="text-xs text-gray-600 mb-1">Withdrawal</p>
                <p className="font-bold text-lg">{selectedWithdrawalRequest?.username}</p>
                <p className="text-sm text-blue-600 mt-1">
                  Available: {formatCurrency(parseFloat(selectedWithdrawalRequest?.amount_remaining || '0'), selectedCurrency)}
                </p>
              </div>
            </div>

            {/* Amount Input */}
            <div>
              <Label htmlFor="match-amount">Match Amount</Label>
              <div className="flex gap-2 mt-2">
                <Input
                  id="match-amount"
                  type="number"
                  placeholder="Enter amount to match"
                  value={matchAmount}
                  onChange={(e) => setMatchAmount(e.target.value)}
                  max={maxMatchAmount}
                  step="0.01"
                />
                <Button
                  onClick={handleQuickMatch}
                  variant="outline"
                  type="button"
                >
                  Max: {formatCurrency(maxMatchAmount, selectedCurrency)}
                </Button>
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Maximum: {formatCurrency(maxMatchAmount, selectedCurrency)}
              </p>
            </div>

            {/* Match Button */}
            <Button
              onClick={handleMatch}
              disabled={matching || !matchAmount || parseFloat(matchAmount) <= 0}
              className="w-full bg-green-600 hover:bg-green-700"
              size="lg"
            >
              <Shuffle className="h-5 w-5 mr-2" />
              {matching ? 'Creating Match...' : `Match ${matchAmount ? formatCurrency(parseFloat(matchAmount), selectedCurrency) : ''}`}
            </Button>
          </CardContent>
        </Card>
      )}

      {!selectedFunding && !selectedWithdrawal && fundingRequests.length > 0 && withdrawalRequests.length > 0 && (
        <Card className="border-gray-200">
          <CardContent className="pt-6 text-center py-8">
            <Shuffle className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">
              Select one funding request and one withdrawal request to create a match
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

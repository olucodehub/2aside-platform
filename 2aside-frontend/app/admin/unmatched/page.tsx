'use client'

import { useState, useEffect } from 'react'
import { Users, Phone, ArrowDownCircle, ArrowUpCircle, RefreshCw, Wallet as WalletIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { adminService, handleApiError, UnmatchedRequest } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { useWalletStore } from '@/lib/store'

export default function UnmatchedUsersPage() {
  const { selectedCurrency, setSelectedCurrency } = useWalletStore()
  const [fundingRequests, setFundingRequests] = useState<UnmatchedRequest[]>([])
  const [withdrawalRequests, setWithdrawalRequests] = useState<UnmatchedRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [matchingWith, setMatchingWith] = useState<string | null>(null)

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

  const handleMatchWithAdminWallet = async (requestId: string, requestType: 'funding' | 'withdrawal') => {
    const typeLabel = requestType === 'funding' ? 'funding' : 'withdrawal'
    if (!confirm(`Are you sure you want to match this ${typeLabel} request with the admin wallet?`)) {
      return
    }

    try {
      setMatchingWith(requestId)
      await adminService.matchWithAdminWallet(requestId, requestType)
      alert('Successfully matched with admin wallet!')
      fetchUnmatchedRequests()
    } catch (err) {
      alert(handleApiError(err))
    } finally {
      setMatchingWith(null)
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
          <h1 className="text-3xl font-bold text-gray-900">Unmatched Requests</h1>
          <p className="mt-2 text-gray-600">
            Users waiting for matching in the next merge cycle
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

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="pt-6">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600">Unmatched Funding Requests</p>
                <p className="text-3xl font-bold text-orange-600">{fundingRequests.length}</p>
              </div>
              <ArrowDownCircle className="h-12 w-12 text-orange-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600">Unmatched Withdrawal Requests</p>
                <p className="text-3xl font-bold text-blue-600">{withdrawalRequests.length}</p>
              </div>
              <ArrowUpCircle className="h-12 w-12 text-blue-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Funding Requests */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ArrowDownCircle className="h-5 w-5 text-orange-600" />
            Funding Requests ({selectedCurrency})
          </CardTitle>
          <CardDescription>
            Users wanting to deposit money - waiting to be matched with withdrawers
          </CardDescription>
        </CardHeader>
        <CardContent>
          {fundingRequests.length === 0 ? (
            <p className="text-center text-gray-500 py-8">
              No unmatched funding requests for {selectedCurrency}
            </p>
          ) : (
            <div className="space-y-3">
              {fundingRequests.map((request) => (
                <div key={request.id} className="border rounded-lg p-4 bg-white flex justify-between items-center">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Users className="h-5 w-5 text-gray-500" />
                      <div>
                        <p className="font-semibold text-lg">{request.username}</p>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Phone className="h-3 w-3" />
                          <span>{request.phone}</span>
                        </div>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm mt-3 pt-3 border-t">
                      <div>
                        <span className="text-gray-500">Total Amount:</span>
                        <p className="font-semibold">{formatCurrency(parseFloat(request.amount), selectedCurrency)}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Remaining:</span>
                        <p className="font-semibold text-orange-600">{formatCurrency(parseFloat(request.amount_remaining), selectedCurrency)}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Requested:</span>
                        <p className="font-semibold">{new Date(request.requested_at).toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                  <div className="ml-4">
                    <Button
                      onClick={() => handleMatchWithAdminWallet(request.id, 'funding')}
                      disabled={matchingWith === request.id}
                      size="sm"
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <WalletIcon className="h-4 w-4 mr-2" />
                      {matchingWith === request.id ? 'Matching...' : 'Match with Admin Wallet'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Withdrawal Requests */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ArrowUpCircle className="h-5 w-5 text-blue-600" />
            Withdrawal Requests ({selectedCurrency})
          </CardTitle>
          <CardDescription>
            Users wanting to withdraw money - waiting to be matched with funders
          </CardDescription>
        </CardHeader>
        <CardContent>
          {withdrawalRequests.length === 0 ? (
            <p className="text-center text-gray-500 py-8">
              No unmatched withdrawal requests for {selectedCurrency}
            </p>
          ) : (
            <div className="space-y-3">
              {withdrawalRequests.map((request) => (
                <div key={request.id} className="border rounded-lg p-4 bg-white flex justify-between items-center">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Users className="h-5 w-5 text-gray-500" />
                      <div>
                        <p className="font-semibold text-lg">{request.username}</p>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Phone className="h-3 w-3" />
                          <span>{request.phone}</span>
                        </div>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm mt-3 pt-3 border-t">
                      <div>
                        <span className="text-gray-500">Total Amount:</span>
                        <p className="font-semibold">{formatCurrency(parseFloat(request.amount), selectedCurrency)}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Remaining:</span>
                        <p className="font-semibold text-blue-600">{formatCurrency(parseFloat(request.amount_remaining), selectedCurrency)}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Requested:</span>
                        <p className="font-semibold">{new Date(request.requested_at).toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                  <div className="ml-4">
                    <Button
                      onClick={() => handleMatchWithAdminWallet(request.id, 'withdrawal')}
                      disabled={matchingWith === request.id}
                      size="sm"
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <WalletIcon className="h-4 w-4 mr-2" />
                      {matchingWith === request.id ? 'Matching...' : 'Match with Admin Wallet'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

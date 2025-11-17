'use client'

import { useState, useEffect } from 'react'
import { Clock, Wallet, Users, TrendingUp, RefreshCw, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { adminService, handleApiError, AdminDashboard, AdminWallet, MergeCycleStats } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'

function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

export default function AdminDashboardPage() {
  const [dashboard, setDashboard] = useState<AdminDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [error, setError] = useState('')
  const [timeRemaining, setTimeRemaining] = useState<number>(0)

  useEffect(() => {
    fetchDashboard()
    const interval = setInterval(fetchDashboard, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (dashboard?.next_merge_cycle) {
      const now = new Date().getTime()
      const mergeTime = new Date(dashboard.next_merge_cycle.scheduled_time).getTime()
      const remaining = Math.max(0, Math.floor((mergeTime - now) / 1000))
      setTimeRemaining(remaining)

      const interval = setInterval(() => {
        setTimeRemaining(prev => Math.max(0, prev - 1))
      }, 1000)

      return () => clearInterval(interval)
    }
  }, [dashboard?.next_merge_cycle])

  const fetchDashboard = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await adminService.getDashboard()
      setDashboard(response.data.data)
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setLoading(false)
    }
  }

  const handleTriggerMergeCycle = async () => {
    if (!confirm('Are you sure you want to manually trigger the next merge cycle? This will execute matching immediately.')) {
      return
    }

    try {
      setTriggering(true)
      await adminService.triggerMergeCycle()
      alert('Merge cycle triggered successfully! Refresh to see results.')
      fetchDashboard()
    } catch (err) {
      alert(handleApiError(err))
    } finally {
      setTriggering(false)
    }
  }

  if (loading && !dashboard) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    )
  }

  if (error && !dashboard) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={fetchDashboard}>Try Again</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const nairaPools = dashboard?.admin_wallets.filter(w => w.currency === 'NAIRA') || []
  const usdtPools = dashboard?.admin_wallets.filter(w => w.currency === 'USDT') || []

  const nairaDashboard = {
    funding_pool: nairaPools.find(w => w.wallet_type === 'funding_pool'),
    platform_fees: nairaPools.find(w => w.wallet_type === 'platform_fees'),
  }

  const usdtDashboard = {
    funding_pool: usdtPools.find(w => w.wallet_type === 'funding_pool'),
    platform_fees: usdtPools.find(w => w.wallet_type === 'platform_fees'),
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="mt-2 text-gray-600">
            Platform overview and batch matching management
          </p>
        </div>
        <Button onClick={fetchDashboard} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Next Merge Cycle */}
      {dashboard?.next_merge_cycle && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Next Merge Cycle
                </CardTitle>
                <CardDescription>
                  Scheduled: {new Date(dashboard.next_merge_cycle.scheduled_time).toLocaleString()}
                </CardDescription>
              </div>
              <Button
                onClick={handleTriggerMergeCycle}
                disabled={triggering}
                size="sm"
                className="bg-orange-600 hover:bg-orange-700"
              >
                <Zap className="h-4 w-4 mr-2" />
                {triggering ? 'Triggering...' : 'Trigger Now'}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <span className="text-sm text-gray-600">Time Remaining:</span>
                <p className="text-2xl font-bold text-blue-600">{formatTime(timeRemaining)}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Status:</span>
                <p className="text-lg font-semibold capitalize">{dashboard.next_merge_cycle.status}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Cutoff Time:</span>
                <p className="text-sm font-medium">
                  {new Date(dashboard.next_merge_cycle.cutoff_time).toLocaleTimeString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Admin Wallets - NAIRA */}
      <div>
        <h2 className="text-xl font-semibold mb-4">NAIRA Admin Wallets</h2>
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Wallet className="h-5 w-5 text-green-600" />
                Funding Pool
              </CardTitle>
              <CardDescription>Available for user withdrawals</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-600">Current Balance:</span>
                  <p className="text-3xl font-bold text-gray-900">
                    {nairaDashboard.funding_pool ? formatCurrency(parseFloat(nairaDashboard.funding_pool.balance), 'NAIRA') : formatCurrency(0, 'NAIRA')}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-3 border-t">
                  <div>
                    <span className="text-xs text-gray-500">Total Funded:</span>
                    <p className="text-sm font-semibold">
                      {nairaDashboard.funding_pool?.total_funded ? formatCurrency(parseFloat(nairaDashboard.funding_pool.total_funded), 'NAIRA') : formatCurrency(0, 'NAIRA')}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Total Received:</span>
                    <p className="text-sm font-semibold">
                      {nairaDashboard.funding_pool?.total_received ? formatCurrency(parseFloat(nairaDashboard.funding_pool.total_received), 'NAIRA') : formatCurrency(0, 'NAIRA')}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-600" />
                Platform Fees
              </CardTitle>
              <CardDescription>Collected transaction fees</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-600">Current Balance:</span>
                  <p className="text-3xl font-bold text-gray-900">
                    {nairaDashboard.platform_fees ? formatCurrency(parseFloat(nairaDashboard.platform_fees.balance), 'NAIRA') : formatCurrency(0, 'NAIRA')}
                  </p>
                </div>
                <div className="pt-3 border-t">
                  <span className="text-xs text-gray-500">Total Fees Collected:</span>
                  <p className="text-sm font-semibold">
                    {nairaDashboard.platform_fees?.total_fees_collected ? formatCurrency(parseFloat(nairaDashboard.platform_fees.total_fees_collected), 'NAIRA') : formatCurrency(0, 'NAIRA')}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Admin Wallets - USDT */}
      <div>
        <h2 className="text-xl font-semibold mb-4">USDT Admin Wallets</h2>
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Wallet className="h-5 w-5 text-green-600" />
                Funding Pool
              </CardTitle>
              <CardDescription>Available for user withdrawals</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-600">Current Balance:</span>
                  <p className="text-3xl font-bold text-gray-900">
                    {usdtDashboard.funding_pool ? formatCurrency(parseFloat(usdtDashboard.funding_pool.balance), 'USDT') : formatCurrency(0, 'USDT')}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-3 border-t">
                  <div>
                    <span className="text-xs text-gray-500">Total Funded:</span>
                    <p className="text-sm font-semibold">
                      {usdtDashboard.funding_pool?.total_funded ? formatCurrency(parseFloat(usdtDashboard.funding_pool.total_funded), 'USDT') : formatCurrency(0, 'USDT')}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Total Received:</span>
                    <p className="text-sm font-semibold">
                      {usdtDashboard.funding_pool?.total_received ? formatCurrency(parseFloat(usdtDashboard.funding_pool.total_received), 'USDT') : formatCurrency(0, 'USDT')}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-600" />
                Platform Fees
              </CardTitle>
              <CardDescription>Collected transaction fees</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-600">Current Balance:</span>
                  <p className="text-3xl font-bold text-gray-900">
                    {usdtDashboard.platform_fees ? formatCurrency(parseFloat(usdtDashboard.platform_fees.balance), 'USDT') : formatCurrency(0, 'USDT')}
                  </p>
                </div>
                <div className="pt-3 border-t">
                  <span className="text-xs text-gray-500">Total Fees Collected:</span>
                  <p className="text-sm font-semibold">
                    {usdtDashboard.platform_fees?.total_fees_collected ? formatCurrency(parseFloat(usdtDashboard.platform_fees.total_fees_collected), 'USDT') : formatCurrency(0, 'USDT')}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Unmatched Requests Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Unmatched Requests
          </CardTitle>
          <CardDescription>Users waiting for matching in next cycle</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-sm text-gray-600">Funding (NAIRA)</p>
              <p className="text-2xl font-bold text-orange-600">
                {dashboard?.unmatched_counts.funding_naira || 0}
              </p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600">Withdrawal (NAIRA)</p>
              <p className="text-2xl font-bold text-blue-600">
                {dashboard?.unmatched_counts.withdrawal_naira || 0}
              </p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-sm text-gray-600">Funding (USDT)</p>
              <p className="text-2xl font-bold text-orange-600">
                {dashboard?.unmatched_counts.funding_usdt || 0}
              </p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600">Withdrawal (USDT)</p>
              <p className="text-2xl font-bold text-blue-600">
                {dashboard?.unmatched_counts.withdrawal_usdt || 0}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Merge Cycles */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Merge Cycles</CardTitle>
          <CardDescription>Last 5 executed merge cycles</CardDescription>
        </CardHeader>
        <CardContent>
          {dashboard?.recent_cycles && dashboard.recent_cycles.length > 0 ? (
            <div className="space-y-3">
              {dashboard.recent_cycles.map((cycle) => (
                <div key={cycle.id} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <p className="font-semibold">
                        {new Date(cycle.scheduled_time).toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-600">
                        Status: <span className="capitalize font-medium">{cycle.status}</span>
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">Matched Pairs</p>
                      <p className="text-2xl font-bold text-green-600">{cycle.matched_pairs}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-4 text-sm pt-3 border-t">
                    <div>
                      <span className="text-gray-500">Funding Requests:</span>
                      <p className="font-semibold">{cycle.total_funding_requests}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Withdrawal Requests:</span>
                      <p className="font-semibold">{cycle.total_withdrawal_requests}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Unmatched Funding:</span>
                      <p className="font-semibold text-orange-600">{cycle.unmatched_funding}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Unmatched Withdrawal:</span>
                      <p className="font-semibold text-orange-600">{cycle.unmatched_withdrawal}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-500 py-8">No merge cycles executed yet</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

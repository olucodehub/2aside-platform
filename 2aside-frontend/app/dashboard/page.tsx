'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowUpRight, ArrowDownRight, TrendingUp, Trophy, Gift, Copy, Check } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { walletService, userService, handleApiError } from '@/lib/api'
import { useWalletStore, useAuthStore } from '@/lib/store'
import { formatCurrency } from '@/lib/utils'
import JoinMergeCycleBanner from '@/components/JoinMergeCycleBanner'
import NextMergeCycleCountdown from '@/components/NextMergeCycleCountdown'

interface WalletStats {
  balance: number
  total_deposited: number
  total_won: number
  total_withdrawn: number
  active_bets: number
  win_rate: number
  referral_code?: string
}

export default function DashboardPage() {
  const { selectedCurrency, getCurrentWallet } = useWalletStore()
  const { user } = useAuthStore()
  const [stats, setStats] = useState<WalletStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  const currentWallet = getCurrentWallet()
  const isBlocked = currentWallet?.is_blocked || false

  useEffect(() => {
    fetchWalletStats()
  }, [selectedCurrency, user])

  const fetchWalletStats = async () => {
    try {
      setLoading(true)

      // Fetch user profile for referral code
      const userResponse = await userService.getProfile()
      const referralCode = userResponse.data.user.referral_code

      // Try to fetch wallet stats (may not exist yet)
      try {
        const walletResponse = await walletService.getWallet(selectedCurrency)
        const wallet = walletResponse.data.wallet || walletResponse.data

        setStats({
          balance: parseFloat(wallet.balance) || 0,
          total_deposited: parseFloat(wallet.total_deposited) || 0,
          total_won: parseFloat(wallet.total_won) || 0,
          total_withdrawn: parseFloat(wallet.total_withdrawn) || 0,
          active_bets: 0, // TODO: Fetch from betting service
          win_rate: 0, // TODO: Calculate from bet history
          referral_code: referralCode, // From user service
        })
      } catch (walletError) {
        // Wallet doesn't exist yet - show defaults but still show referral code
        console.log('Wallet not found, showing defaults')
        setStats({
          balance: 0,
          total_deposited: 0,
          total_won: 0,
          total_withdrawn: 0,
          active_bets: 0,
          win_rate: 0,
          referral_code: referralCode, // From user service
        })
      }
    } catch (error) {
      console.error('Error fetching stats:', handleApiError(error))
      // Set error state
      setStats({
        balance: 0,
        total_deposited: 0,
        total_won: 0,
        total_withdrawn: 0,
        active_bets: 0,
        win_rate: 0,
        referral_code: 'Error loading',
      })
    } finally {
      setLoading(false)
    }
  }

  const copyReferralCode = () => {
    if (stats?.referral_code) {
      navigator.clipboard.writeText(stats.referral_code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 rounded bg-gray-200"></div>
            </CardHeader>
            <CardContent>
              <div className="h-8 w-32 rounded bg-gray-200"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Next Merge Cycle Countdown */}
      <NextMergeCycleCountdown />

      {/* Join Merge Cycle Banner */}
      <JoinMergeCycleBanner />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Balance</CardTitle>
            <TrendingUp className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(stats?.balance || 0, selectedCurrency)}
            </div>
            <p className="text-xs text-gray-500">Available funds</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Deposited</CardTitle>
            <ArrowDownRight className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(stats?.total_deposited || 0, selectedCurrency)}
            </div>
            <p className="text-xs text-gray-500">All-time deposits</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Won</CardTitle>
            <Trophy className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(stats?.total_won || 0, selectedCurrency)}
            </div>
            <p className="text-xs text-gray-500">Winnings</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Withdrawn</CardTitle>
            <ArrowUpRight className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(stats?.total_withdrawn || 0, selectedCurrency)}
            </div>
            <p className="text-xs text-gray-500">All-time withdrawals</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Link href={isBlocked ? '#' : '/dashboard/funding/request'} className={isBlocked ? 'pointer-events-none' : ''}>
              <Button variant="default" className="w-full" disabled={isBlocked} title={isBlocked ? 'Account blocked - Cannot perform this action' : ''}>
                <ArrowDownRight className="mr-2 h-4 w-4" />
                Fund Wallet
              </Button>
            </Link>
            <Link href={isBlocked ? '#' : '/dashboard/funding/withdraw'} className={isBlocked ? 'pointer-events-none' : ''}>
              <Button variant="secondary" className="w-full" disabled={isBlocked} title={isBlocked ? 'Account blocked - Cannot perform this action' : ''}>
                <ArrowUpRight className="mr-2 h-4 w-4" />
                Withdraw
              </Button>
            </Link>
            <Link href={isBlocked ? '#' : '/dashboard/games'} className={isBlocked ? 'pointer-events-none' : ''}>
              <Button variant="outline" className="w-full" disabled={isBlocked} title={isBlocked ? 'Account blocked - Cannot perform this action' : ''}>
                <Trophy className="mr-2 h-4 w-4" />
                Place Bet
              </Button>
            </Link>
            <Link href="/dashboard/history">
              <Button variant="ghost" className="w-full">
                View History
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Referral Card */}
        <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Gift className="h-5 w-5 text-purple-600" />
              <CardTitle className="text-purple-900">Refer Friends & Earn</CardTitle>
            </div>
            <CardDescription className="text-purple-700">
              Earn 5% of platform fees from your friends' first win!
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="rounded-lg bg-white border border-purple-200 p-4">
                <p className="text-xs font-medium text-gray-600 mb-2">Your Referral Code</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-2xl font-bold text-purple-600 tracking-wider">
                    {stats?.referral_code || 'Loading...'}
                  </code>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={copyReferralCode}
                    className="shrink-0"
                  >
                    {copied ? (
                      <>
                        <Check className="h-4 w-4 mr-1" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4 mr-1" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
              </div>
              <div className="text-sm text-purple-800 space-y-1">
                <p><strong>How it works:</strong></p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>Share your referral code with friends</li>
                  <li>They use it when registering</li>
                  <li>When they win their first bet, you earn 5% of the platform fee!</li>
                  <li>Bonus credited automatically to your wallet</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* P2P Funding Info */}
        <Card className="border-emerald-200 bg-emerald-50">
          <CardHeader>
            <CardTitle className="text-emerald-900">How P2P Funding Works</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-emerald-800">
              <p>
                <strong>Instant Matching:</strong> When you request to fund your wallet, you're matched
                with someone who wants to withdraw. This creates a peer-to-peer transaction.
              </p>
              <p>
                <strong>Secure Process:</strong> Send payment to your matched partner, upload proof,
                and receive confirmation. Funds are credited to your wallet immediately after confirmation.
              </p>
              <p>
                <strong>Multiple Currencies:</strong> Support for both Nigerian Naira (₦) and USDT ($).
                Switch between currencies anytime using the toggle above.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

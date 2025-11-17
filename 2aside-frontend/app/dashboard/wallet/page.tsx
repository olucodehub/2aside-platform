'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Wallet, TrendingUp, TrendingDown, ArrowDownRight, ArrowUpRight, RefreshCw, Building2, Shield, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { walletService, handleApiError } from '@/lib/api'
import { useWalletStore } from '@/lib/store'
import { formatCurrency, formatDate } from '@/lib/utils'

interface Transaction {
  id: string
  wallet_id: string
  type: string
  amount: number
  balance_before: number
  balance_after: number
  description: string
  created_at: string
}

interface BankAccount {
  has_bank_account: boolean
  account_number?: string
  account_name?: string
  bank_name?: string
}

interface UsdtAddress {
  has_wallet_address: boolean
  wallet_address?: string
  network?: string
}

export default function WalletPage() {
  const { selectedCurrency, nairaWallet, usdtWallet, setNairaWallet, setUsdtWallet } = useWalletStore()
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  // Bank account state
  const [bankAccount, setBankAccount] = useState<BankAccount | null>(null)
  const [showBankForm, setShowBankForm] = useState(false)
  const [bankFormData, setBankFormData] = useState({
    account_number: '',
    account_name: '',
    bank_name: ''
  })
  const [bankFormLoading, setBankFormLoading] = useState(false)
  const [bankError, setBankError] = useState('')

  // USDT address state
  const [usdtAddress, setUsdtAddress] = useState<UsdtAddress | null>(null)
  const [showUsdtForm, setShowUsdtForm] = useState(false)
  const [usdtAddressInput, setUsdtAddressInput] = useState('')
  const [usdtFormLoading, setUsdtFormLoading] = useState(false)
  const [usdtError, setUsdtError] = useState('')

  const currentWallet = selectedCurrency === 'NAIRA' ? nairaWallet : usdtWallet

  useEffect(() => {
    fetchWalletData()
  }, [selectedCurrency])

  const fetchWalletData = async () => {
    try {
      setLoading(true)

      // Fetch wallet and transactions
      const [walletRes, transactionsRes] = await Promise.all([
        walletService.getWallet(selectedCurrency),
        walletService.getTransactions(selectedCurrency, 10),
      ])

      const wallet = walletRes.data.data?.wallet || walletRes.data
      if (selectedCurrency === 'NAIRA') {
        setNairaWallet(wallet)
      } else {
        setUsdtWallet(wallet)
      }

      const txData = transactionsRes.data.data?.transactions || transactionsRes.data
      setTransactions(Array.isArray(txData) ? txData : [])

      // Fetch bank account or USDT address based on currency
      if (selectedCurrency === 'NAIRA') {
        try {
          const bankRes = await walletService.getNairaBankAccount()
          // Handle different possible response structures
          const bankData = bankRes.data?.data || bankRes.data
          setBankAccount(bankData)
        } catch (error) {
          setBankAccount({ has_bank_account: false })
        }
      } else {
        try {
          const usdtRes = await walletService.getUsdtWalletAddress()
          // Handle different possible response structures
          const usdtData = usdtRes.data?.data || usdtRes.data
          setUsdtAddress(usdtData)
        } catch (error) {
          setUsdtAddress({ has_wallet_address: false })
        }
      }
    } catch (error) {
      console.error('Error fetching wallet data:', handleApiError(error))
    } finally {
      setLoading(false)
    }
  }

  const handleBankAccountSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBankError('')
    setBankFormLoading(true)

    try {
      await walletService.setNairaBankAccount(bankFormData)
      // Refresh bank account data
      const bankRes = await walletService.getNairaBankAccount()
      const bankData = bankRes.data?.data || bankRes.data
      setBankAccount(bankData)
      setShowBankForm(false)
      setBankFormData({ account_number: '', account_name: '', bank_name: '' })
    } catch (error) {
      setBankError(handleApiError(error))
    } finally {
      setBankFormLoading(false)
    }
  }

  const handleUsdtAddressSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setUsdtError('')
    setUsdtFormLoading(true)

    try {
      await walletService.setUsdtWalletAddress(usdtAddressInput)
      // Refresh USDT address data
      const usdtRes = await walletService.getUsdtWalletAddress()
      const usdtData = usdtRes.data?.data || usdtRes.data
      setUsdtAddress(usdtData)
      setShowUsdtForm(false)
      setUsdtAddressInput('')
    } catch (error) {
      setUsdtError(handleApiError(error))
    } finally {
      setUsdtFormLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchWalletData()
    setRefreshing(false)
  }

  const getTransactionIcon = (type: string) => {
    if (type === 'deposit' || type === 'win' || type === 'referral_bonus') {
      return <TrendingUp className="h-4 w-4 text-green-600" />
    }
    return <TrendingDown className="h-4 w-4 text-red-600" />
  }

  const getTransactionColor = (type: string) => {
    if (type === 'deposit' || type === 'win' || type === 'referral_bonus') {
      return 'text-green-600'
    }
    return 'text-red-600'
  }

  if (loading || !currentWallet) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 animate-pulse rounded bg-gray-200"></div>
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 w-24 rounded bg-gray-200"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 w-32 rounded bg-gray-200"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Wallet Overview</h1>
          <p className="mt-2 text-gray-600">
            {selectedCurrency} Wallet
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Balance</CardTitle>
            <Wallet className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {formatCurrency(currentWallet?.balance || 0, selectedCurrency)}
            </div>
            <p className="text-xs text-gray-500 mt-1">Available to bet or withdraw</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Deposited</CardTitle>
            <ArrowDownRight className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {formatCurrency(currentWallet?.total_deposited || 0, selectedCurrency)}
            </div>
            <p className="text-xs text-gray-500 mt-1">All-time deposits</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Won</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {formatCurrency(currentWallet?.total_won || 0, selectedCurrency)}
            </div>
            <p className="text-xs text-gray-500 mt-1">Winnings from bets</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            <Link href="/dashboard/funding/request">
              <Button className="w-full">
                <ArrowDownRight className="mr-2 h-4 w-4" />
                Fund Wallet
              </Button>
            </Link>
            <Link href="/dashboard/funding/withdraw">
              <Button variant="secondary" className="w-full">
                <ArrowUpRight className="mr-2 h-4 w-4" />
                Withdraw Funds
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Wallet Info */}
      <Card>
        <CardHeader>
          <CardTitle>Wallet Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Wallet ID</span>
            <span className="text-sm font-mono text-gray-900">
              {currentWallet?.id ? currentWallet.id.slice(0, 8) : 'N/A'}...
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Currency</span>
            <span className="text-sm font-medium text-gray-900">{selectedCurrency}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Referral Code</span>
            <span className="text-sm font-mono font-medium text-emerald-600">
              {currentWallet?.referral_code || 'N/A'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Total Withdrawn</span>
            <span className="text-sm font-medium text-gray-900">
              {formatCurrency(currentWallet?.total_withdrawn || 0, selectedCurrency)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Status</span>
            <span className={`text-sm font-medium ${currentWallet?.is_blocked ? 'text-red-600' : 'text-green-600'}`}>
              {currentWallet?.is_blocked ? 'Blocked' : 'Active'}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Bank Account Details (NAIRA only) */}
      {selectedCurrency === 'NAIRA' && bankAccount && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-blue-600" />
                <CardTitle>Bank Account Details</CardTitle>
              </div>
              {!bankAccount.has_bank_account && (
                <Button size="sm" onClick={() => setShowBankForm(!showBankForm)}>
                  {showBankForm ? 'Cancel' : 'Add Bank Account'}
                </Button>
              )}
            </div>
            <CardDescription>
              {bankAccount.has_bank_account
                ? 'Your NAIRA withdrawal bank account'
                : 'Add your bank account for NAIRA withdrawals'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {bankAccount.has_bank_account ? (
              <div className="space-y-3">
                <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                  <div className="flex items-start gap-2 mb-3">
                    <Shield className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-green-900">Bank account verified</p>
                      <p className="text-xs text-green-700">This account cannot be changed for security reasons</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Account Name</span>
                      <span className="text-sm font-medium text-gray-900">{bankAccount.account_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Account Number</span>
                      <span className="text-sm font-mono font-medium text-gray-900">{bankAccount.account_number}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Bank Name</span>
                      <span className="text-sm font-medium text-gray-900">{bankAccount.bank_name}</span>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  All NAIRA withdrawals will be sent to this account. Contact support if you need to change it.
                </p>
              </div>
            ) : showBankForm ? (
              <form onSubmit={handleBankAccountSubmit} className="space-y-4">
                {bankError && (
                  <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
                    {bankError}
                  </div>
                )}
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5" />
                    <div className="text-xs text-amber-800">
                      <strong>Important:</strong> Account name must contain your registered first and last name.
                      This cannot be changed once submitted.
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="account_name">Account Name</Label>
                  <Input
                    id="account_name"
                    value={bankFormData.account_name}
                    onChange={(e) => setBankFormData({ ...bankFormData, account_name: e.target.value })}
                    placeholder="John Doe"
                    required
                    disabled={bankFormLoading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="account_number">Account Number</Label>
                  <Input
                    id="account_number"
                    value={bankFormData.account_number}
                    onChange={(e) => setBankFormData({ ...bankFormData, account_number: e.target.value })}
                    placeholder="0123456789"
                    required
                    disabled={bankFormLoading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="bank_name">Bank Name</Label>
                  <Input
                    id="bank_name"
                    value={bankFormData.bank_name}
                    onChange={(e) => setBankFormData({ ...bankFormData, bank_name: e.target.value })}
                    placeholder="Access Bank"
                    required
                    disabled={bankFormLoading}
                  />
                </div>
                <Button type="submit" className="w-full" disabled={bankFormLoading}>
                  {bankFormLoading ? 'Saving...' : 'Save Bank Account'}
                </Button>
              </form>
            ) : (
              <p className="text-center text-sm text-gray-500 py-4">
                No bank account added yet. Click "Add Bank Account" to add one.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* USDT Wallet Address (USDT only) */}
      {selectedCurrency === 'USDT' && usdtAddress && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Wallet className="h-5 w-5 text-blue-600" />
                <CardTitle>USDT Wallet Address</CardTitle>
              </div>
              {!usdtAddress.has_wallet_address && (
                <Button size="sm" onClick={() => setShowUsdtForm(!showUsdtForm)}>
                  {showUsdtForm ? 'Cancel' : 'Add Wallet Address'}
                </Button>
              )}
            </div>
            <CardDescription>
              {usdtAddress.has_wallet_address
                ? 'Your BEP20 USDT withdrawal address'
                : 'Add your BEP20 USDT wallet address for withdrawals'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {usdtAddress.has_wallet_address ? (
              <div className="space-y-3">
                <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                  <div className="flex items-start gap-2 mb-3">
                    <Shield className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-green-900">Wallet address verified</p>
                      <p className="text-xs text-green-700">This address cannot be changed for security reasons</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Wallet Address</span>
                    </div>
                    <div className="rounded bg-white p-2 border border-gray-200">
                      <code className="text-xs font-mono text-gray-900 break-all">{usdtAddress.wallet_address}</code>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Network</span>
                      <span className="text-sm font-medium text-gray-900">{usdtAddress.network || 'BEP20 (BSC)'}</span>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  All USDT withdrawals will be sent to this address. Contact support if you need to change it.
                </p>
              </div>
            ) : showUsdtForm ? (
              <form onSubmit={handleUsdtAddressSubmit} className="space-y-4">
                {usdtError && (
                  <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
                    {usdtError}
                  </div>
                )}
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5" />
                    <div className="text-xs text-amber-800">
                      <strong>Important:</strong> Enter a valid BEP20 (Binance Smart Chain) USDT address.
                      Address must start with "0x" and be 42 characters long. This cannot be changed once submitted.
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="wallet_address">BEP20 Wallet Address</Label>
                  <Input
                    id="wallet_address"
                    value={usdtAddressInput}
                    onChange={(e) => setUsdtAddressInput(e.target.value)}
                    placeholder="0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
                    required
                    disabled={usdtFormLoading}
                    className="font-mono text-sm"
                  />
                  <p className="text-xs text-gray-500">
                    Make sure this is a BEP20 address. Sending to wrong network will result in loss of funds.
                  </p>
                </div>
                <Button type="submit" className="w-full" disabled={usdtFormLoading}>
                  {usdtFormLoading ? 'Saving...' : 'Save Wallet Address'}
                </Button>
              </form>
            ) : (
              <p className="text-center text-sm text-gray-500 py-4">
                No wallet address added yet. Click "Add Wallet Address" to add one.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Recent Transactions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Transactions</CardTitle>
              <CardDescription>Last 10 transactions on this wallet</CardDescription>
            </div>
            <Link href="/dashboard/history">
              <Button variant="ghost" size="sm">
                View All
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          {transactions.length === 0 ? (
            <p className="text-center text-sm text-gray-500 py-8">No transactions yet</p>
          ) : (
            <div className="space-y-3">
              {transactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex items-center justify-between border-b border-gray-100 pb-3 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    {getTransactionIcon(transaction.type)}
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {transaction.description || transaction.type}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatDate(transaction.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-semibold ${getTransactionColor(transaction.type)}`}>
                      {transaction.type === 'deposit' || transaction.type === 'win' || transaction.type === 'referral_bonus' ? '+' : '-'}
                      {formatCurrency(Math.abs(transaction.amount), selectedCurrency)}
                    </p>
                    <p className="text-xs text-gray-500">
                      Balance: {formatCurrency(transaction.balance_after, selectedCurrency)}
                    </p>
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

'use client'

import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, Filter } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
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
  description: string | null
  reference: string | null
  created_at: string
}

const TRANSACTION_TYPES = [
  { value: 'all', label: 'All Transactions' },
  { value: 'deposit', label: 'Deposits' },
  { value: 'withdrawal', label: 'Withdrawals' },
  { value: 'win', label: 'Winnings' },
  { value: 'bet_debit', label: 'Bet Placements' },
  { value: 'bet_refund', label: 'Bet Refunds' },
  { value: 'referral_bonus', label: 'Referral Bonuses' },
]

export default function HistoryPage() {
  const { selectedCurrency } = useWalletStore()
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [filteredTransactions, setFilteredTransactions] = useState<Transaction[]>([])
  const [selectedType, setSelectedType] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTransactions()
  }, [selectedCurrency])

  useEffect(() => {
    filterTransactions()
  }, [transactions, selectedType])

  const fetchTransactions = async () => {
    try {
      setLoading(true)
      const response = await walletService.getTransactions(selectedCurrency, 50)
      setTransactions(response.data)
    } catch (error) {
      console.error('Error fetching transactions:', handleApiError(error))
    } finally {
      setLoading(false)
    }
  }

  const filterTransactions = () => {
    if (selectedType === 'all') {
      setFilteredTransactions(transactions)
    } else {
      setFilteredTransactions(transactions.filter(t => t.type === selectedType))
    }
  }

  const getTransactionIcon = (type: string) => {
    if (type === 'deposit' || type === 'win' || type === 'referral_bonus' || type === 'bet_refund') {
      return <TrendingUp className="h-5 w-5 text-green-600" />
    }
    return <TrendingDown className="h-5 w-5 text-red-600" />
  }

  const getTransactionColor = (type: string) => {
    if (type === 'deposit' || type === 'win' || type === 'referral_bonus' || type === 'bet_refund') {
      return 'text-green-600'
    }
    return 'text-red-600'
  }

  const getTransactionBadgeColor = (type: string) => {
    const colors: Record<string, string> = {
      deposit: 'bg-green-100 text-green-800',
      withdrawal: 'bg-red-100 text-red-800',
      win: 'bg-yellow-100 text-yellow-800',
      bet_debit: 'bg-blue-100 text-blue-800',
      bet_refund: 'bg-purple-100 text-purple-800',
      referral_bonus: 'bg-emerald-100 text-emerald-800',
      platform_fee: 'bg-gray-100 text-gray-800',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 animate-pulse rounded bg-gray-200"></div>
        <Card className="animate-pulse">
          <CardHeader>
            <div className="h-4 w-32 rounded bg-gray-200"></div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-16 rounded bg-gray-200"></div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Transaction History</h1>
        <p className="mt-2 text-gray-600">
          View all your {selectedCurrency} transactions
        </p>
      </div>

      {/* Filter */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-600" />
            <CardTitle className="text-base">Filter by Type</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {TRANSACTION_TYPES.map((type) => (
              <Button
                key={type.value}
                variant={selectedType === type.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedType(type.value)}
              >
                {type.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Transactions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{filteredTransactions.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Credits
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(
                filteredTransactions
                  .filter(t => ['deposit', 'win', 'referral_bonus', 'bet_refund'].includes(t.type))
                  .reduce((sum, t) => sum + t.amount, 0),
                selectedCurrency
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Debits
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(
                filteredTransactions
                  .filter(t => ['withdrawal', 'bet_debit', 'platform_fee'].includes(t.type))
                  .reduce((sum, t) => sum + t.amount, 0),
                selectedCurrency
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Transactions List */}
      <Card>
        <CardHeader>
          <CardTitle>Transactions</CardTitle>
          <CardDescription>
            {filteredTransactions.length} transaction(s) found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredTransactions.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No transactions found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredTransactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex items-start justify-between border-b border-gray-100 pb-4 last:border-0 last:pb-0"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1">
                      {getTransactionIcon(transaction.type)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-gray-900">
                          {transaction.description || transaction.type.replace('_', ' ').toUpperCase()}
                        </p>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getTransactionBadgeColor(transaction.type)}`}>
                          {transaction.type.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatDate(transaction.created_at)}
                      </p>
                      {transaction.reference && (
                        <p className="text-xs text-gray-400 mt-0.5 font-mono">
                          Ref: {transaction.reference.slice(0, 12)}...
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="text-right">
                    <p className={`text-base font-bold ${getTransactionColor(transaction.type)}`}>
                      {['deposit', 'win', 'referral_bonus', 'bet_refund'].includes(transaction.type) ? '+' : '-'}
                      {formatCurrency(Math.abs(transaction.amount), selectedCurrency)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
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

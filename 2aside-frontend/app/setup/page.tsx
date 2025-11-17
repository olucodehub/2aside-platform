'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Wallet, Building, CreditCard, ArrowRight, ArrowLeft, CheckCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { walletService, handleApiError } from '@/lib/api'
import { useAuthStore, useWalletStore } from '@/lib/store'

export default function SetupPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const currency = (searchParams.get('currency') || 'NAIRA') as 'NAIRA' | 'USDT'
  const { user } = useAuthStore()
  const { nairaWallet, usdtWallet, fetchWallets } = useWalletStore()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Bank account form (NAIRA)
  const [bankData, setBankData] = useState({
    account_number: '',
    account_name: '',
    bank_name: '',
  })

  // USDT wallet form
  const [walletAddress, setWalletAddress] = useState('')

  // Saved payment details
  const [savedBankDetails, setSavedBankDetails] = useState<any>(null)
  const [savedUsdtAddress, setSavedUsdtAddress] = useState<string | null>(null)
  const [loadingDetails, setLoadingDetails] = useState(true)

  // Check if current currency is already set up
  const isNairaSetup = currency === 'NAIRA' && nairaWallet?.bank_details_id
  const isUsdtSetup = currency === 'USDT' && usdtWallet?.wallet_address

  // Fetch saved payment details when currency changes
  useEffect(() => {
    const fetchPaymentDetails = async () => {
      setLoadingDetails(true)
      setSavedBankDetails(null)
      setSavedUsdtAddress(null)

      try {
        if (currency === 'NAIRA' && nairaWallet?.bank_details_id) {
          const response = await walletService.getNairaBankAccount()
          if (response.data.data?.has_bank_account) {
            setSavedBankDetails(response.data.data)
          }
        } else if (currency === 'USDT' && usdtWallet?.wallet_address) {
          const response = await walletService.getUsdtWalletAddress()
          if (response.data.data?.has_wallet_address) {
            setSavedUsdtAddress(response.data.data.wallet_address)
          }
        }
      } catch (err) {
        // If fetching fails, show form
      } finally {
        setLoadingDetails(false)
      }
    }

    fetchPaymentDetails()
  }, [currency, nairaWallet, usdtWallet])

  const handleBankChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setBankData({ ...bankData, [e.target.name]: e.target.value })
  }

  const handleBankSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!bankData.account_number || !bankData.account_name || !bankData.bank_name) {
      setError('Please fill all required fields')
      return
    }

    setLoading(true)
    try {
      const response = await walletService.setNairaBankAccount(bankData)
      setSuccess('Bank account added successfully!')

      await fetchWallets()
      router.push('/dashboard')
    } catch (err) {
      setError(handleApiError(err))
      setLoading(false)
    }
  }

  const handleUsdtSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!walletAddress.trim()) {
      setError('Please enter a valid USDT wallet address')
      return
    }

    setLoading(true)
    try {
      const response = await walletService.setUsdtWalletAddress(walletAddress)
      setSuccess('USDT wallet address added successfully!')

      await fetchWallets()
      router.push('/dashboard')
    } catch (err) {
      setError(handleApiError(err))
      setLoading(false)
    }
  }

  const switchCurrency = (newCurrency: 'NAIRA' | 'USDT') => {
    router.push(`/setup?currency=${newCurrency}`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Back Button */}
        <Button
          variant="ghost"
          onClick={() => router.push('/dashboard')}
          className="mb-4 flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Button>

        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 rounded-full mb-4">
            <Wallet className="h-8 w-8 text-emerald-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {isNairaSetup || isUsdtSetup ? 'Payment Details' : 'Complete Your Setup'}
          </h1>
          <p className="text-gray-600">
            {isNairaSetup || isUsdtSetup
              ? 'View your saved payment details'
              : 'Add your payment details to start funding and withdrawing'}
          </p>
        </div>

        {/* Currency Switcher */}
        <div className="flex gap-2 mb-4 justify-center">
          <Button
            variant={currency === 'NAIRA' ? 'default' : 'outline'}
            onClick={() => switchCurrency('NAIRA')}
            className="flex items-center gap-2"
          >
            <Building className="h-4 w-4" />
            NAIRA (Bank)
          </Button>
          <Button
            variant={currency === 'USDT' ? 'default' : 'outline'}
            onClick={() => switchCurrency('USDT')}
            className="flex items-center gap-2"
          >
            <CreditCard className="h-4 w-4" />
            USDT (Crypto)
          </Button>
        </div>

        {/* Setup Card */}
        <Card>
          <CardHeader>
            <CardTitle>
              {currency === 'NAIRA' ? 'Bank Account Setup' : 'USDT Wallet Setup'}
            </CardTitle>
            <CardDescription>
              {currency === 'NAIRA'
                ? 'Add your bank account for NAIRA transactions'
                : 'Add your BEP20 USDT wallet address for crypto transactions'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-800">
                {error}
              </div>
            )}
            {success && (
              <div className="mb-4 rounded-md bg-green-50 p-3 text-sm text-green-800">
                {success}
              </div>
            )}

            {currency === 'NAIRA' ? (
              // NAIRA Bank Account - Show saved or form
              loadingDetails ? (
                <div className="text-center py-8 text-gray-500">Loading...</div>
              ) : savedBankDetails ? (
                // Show saved bank details
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-green-600 mb-4">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">Bank account configured</span>
                  </div>

                  <div className="space-y-3 bg-gray-50 p-4 rounded-lg">
                    <div>
                      <Label className="text-gray-600">Account Number</Label>
                      <p className="text-gray-900 font-medium">{savedBankDetails.account_number}</p>
                    </div>

                    <div>
                      <Label className="text-gray-600">Account Name</Label>
                      <p className="text-gray-900 font-medium">{savedBankDetails.account_name}</p>
                    </div>

                    <div>
                      <Label className="text-gray-600">Bank Name</Label>
                      <p className="text-gray-900 font-medium">{savedBankDetails.bank_name}</p>
                    </div>

                  </div>

                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Note:</strong> This bank account is used for receiving withdrawals.
                      Contact support if you need to update these details.
                    </p>
                  </div>

                  <Button
                    onClick={() => router.push('/dashboard')}
                    className="w-full"
                  >
                    Go to Dashboard
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              ) : (
                // Show form for new setup
                <form onSubmit={handleBankSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="account_number">Account Number *</Label>
                    <Input
                      id="account_number"
                      name="account_number"
                      type="text"
                      placeholder="0123456789"
                      value={bankData.account_number}
                      onChange={handleBankChange}
                      disabled={loading}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="account_name">Account Name *</Label>
                    <Input
                      id="account_name"
                      name="account_name"
                      type="text"
                      placeholder="John Doe"
                      value={bankData.account_name}
                      onChange={handleBankChange}
                      disabled={loading}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="bank_name">Bank Name *</Label>
                    <Input
                      id="bank_name"
                      name="bank_name"
                      type="text"
                      placeholder="First Bank of Nigeria"
                      value={bankData.bank_name}
                      onChange={handleBankChange}
                      disabled={loading}
                      required
                    />
                  </div>

                  <Button type="submit" disabled={loading} className="w-full mt-4">
                    {loading ? 'Saving...' : (
                      <>
                        Continue
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </>
                    )}
                  </Button>

                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Note:</strong> This bank account will be used for receiving withdrawals.
                      Make sure the account details are accurate and match your registered name.
                    </p>
                  </div>

                  <div className="mt-4 p-4 bg-amber-50 rounded-lg">
                    <p className="text-sm text-amber-800">
                      <strong>Important:</strong> You must add at least one payment method (Bank Account or USDT Wallet) before you can access the dashboard and start trading.
                    </p>
                  </div>
                </form>
              )
            ) : (
              // USDT Wallet - Show saved or form
              loadingDetails ? (
                <div className="text-center py-8 text-gray-500">Loading...</div>
              ) : savedUsdtAddress ? (
                // Show saved USDT wallet
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-green-600 mb-4">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">USDT wallet configured</span>
                  </div>

                  <div className="space-y-3 bg-gray-50 p-4 rounded-lg">
                    <div>
                      <Label className="text-gray-600">Wallet Address (BEP20)</Label>
                      <p className="text-gray-900 font-mono text-sm break-all">{savedUsdtAddress}</p>
                    </div>

                    <div>
                      <Label className="text-gray-600">Network</Label>
                      <p className="text-gray-900 font-medium">BEP20 (Binance Smart Chain)</p>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Note:</strong> This wallet address is used for receiving USDT withdrawals.
                      Contact support if you need to update this address.
                    </p>
                  </div>

                  <Button
                    onClick={() => router.push('/dashboard')}
                    className="w-full"
                  >
                    Go to Dashboard
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              ) : (
                // Show form for new setup
                <form onSubmit={handleUsdtSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="wallet_address">USDT Wallet Address (BEP20) *</Label>
                    <Input
                      id="wallet_address"
                      name="wallet_address"
                      type="text"
                      placeholder="0x..."
                      value={walletAddress}
                      onChange={(e) => setWalletAddress(e.target.value)}
                      disabled={loading}
                      required
                    />
                    <p className="text-xs text-gray-500">
                      Enter your BEP20 (Binance Smart Chain) USDT wallet address
                    </p>
                  </div>

                  <Button type="submit" disabled={loading} className="w-full mt-4">
                    {loading ? 'Saving...' : (
                      <>
                        Continue
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </>
                    )}
                  </Button>

                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Note:</strong> This wallet address will be used for receiving USDT withdrawals.
                      Please ensure you enter a valid BEP20 (Binance Smart Chain) USDT address starting with &quot;0x&quot;.
                    </p>
                  </div>

                  <div className="mt-4 p-4 bg-amber-50 rounded-lg">
                    <p className="text-sm text-amber-800">
                      <strong>Important:</strong> You must add at least one payment method (Bank Account or USDT Wallet) before you can access the dashboard and start trading.
                    </p>
                  </div>
                </form>
              )
            )}
          </CardContent>
        </Card>

        {/* Additional Info */}
        <div className="mt-6 text-center text-sm text-gray-500">
          {(isNairaSetup || isUsdtSetup) && 'Your payment details are securely stored. Contact support if you need to update them.'}
          {!(isNairaSetup || isUsdtSetup) && 'You can add additional payment methods later from your wallet settings'}
        </div>
      </div>
    </div>
  )
}

'use client'

import { useState, useEffect } from 'react'
import { User, Mail, Phone, Calendar, Copy, Check, Building2, Wallet } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { userService, walletService, handleApiError } from '@/lib/api'
import { useAuthStore, useWalletStore } from '@/lib/store'
import { formatDate } from '@/lib/utils'

interface BankDetails {
  account_number: string
  account_name: string
  bank_name: string
  bank_code?: string
}

interface PaymentDetails {
  naira?: BankDetails
  usdt?: string
}

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore()
  const { nairaWallet, usdtWallet } = useWalletStore()
  const [copied, setCopied] = useState(false)
  const [changingPassword, setChangingPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [paymentDetails, setPaymentDetails] = useState<PaymentDetails>({})
  const [loadingPaymentDetails, setLoadingPaymentDetails] = useState(true)
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Fetch payment details on mount
  useEffect(() => {
    fetchPaymentDetails()
  }, [])

  const fetchPaymentDetails = async () => {
    try {
      setLoadingPaymentDetails(true)
      const details: PaymentDetails = {}

      // Fetch NAIRA wallet details
      try {
        const nairaResponse = await walletService.getWallet('NAIRA')
        const nairaWallet = nairaResponse.data.wallet
        if (nairaWallet?.bank_details) {
          details.naira = nairaWallet.bank_details
        }
      } catch (err) {
        // Wallet doesn't exist yet
        console.log('NAIRA wallet not found')
      }

      // Fetch USDT wallet details
      try {
        const usdtResponse = await walletService.getWallet('USDT')
        const usdtWallet = usdtResponse.data.wallet
        if (usdtWallet?.wallet_address) {
          details.usdt = usdtWallet.wallet_address
        }
      } catch (err) {
        // Wallet doesn't exist yet
        console.log('USDT wallet not found')
      }

      setPaymentDetails(details)
    } catch (err) {
      console.error('Error fetching payment details:', err)
    } finally {
      setLoadingPaymentDetails(false)
    }
  }

  const handleCopyReferralCode = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPasswordData({ ...passwordData, [e.target.name]: e.target.value })
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    // Validate passwords match
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setError('New passwords do not match')
      return
    }

    // Validate password strength
    if (passwordData.newPassword.length < 8) {
      setError('New password must be at least 8 characters long')
      return
    }

    setLoading(true)

    try {
      await userService.changePassword({
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
      })
      setSuccess('Password changed successfully')
      setChangingPassword(false)
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      })
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setLoading(false)
    }
  }

  const handleCancelPasswordChange = () => {
    setPasswordData({
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    })
    setChangingPassword(false)
    setError('')
    setSuccess('')
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
        <p className="mt-2 text-gray-600">
          Manage your account information and referral codes
        </p>
      </div>

      {/* Profile Information */}
      <Card>
        <CardHeader>
          <CardTitle>Personal Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <User className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Username</p>
                <p className="font-medium text-gray-900">{user?.username}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Email</p>
                <p className="font-medium text-gray-900">{user?.email}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Phone className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Phone</p>
                <p className="font-medium text-gray-900">{user?.phone}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Calendar className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-sm text-gray-600">Member Since</p>
                <p className="font-medium text-gray-900">
                  {user?.created_at ? formatDate(user.created_at) : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Payment Details */}
      <Card>
        <CardHeader>
          <CardTitle>Payment Details</CardTitle>
          <CardDescription>
            Your saved bank account and wallet addresses (read-only)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingPaymentDetails ? (
            <div className="space-y-4">
              <div className="animate-pulse rounded-lg bg-gray-200 h-24"></div>
              <div className="animate-pulse rounded-lg bg-gray-200 h-24"></div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* NAIRA Bank Details */}
              {paymentDetails.naira ? (
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <div className="flex items-start gap-3">
                    <Building2 className="h-5 w-5 text-gray-600 mt-1" />
                    <div className="flex-1 space-y-2">
                      <p className="text-sm font-medium text-gray-900">NAIRA Bank Account</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                        <div>
                          <p className="text-gray-600">Bank Name</p>
                          <p className="font-medium text-gray-900">{paymentDetails.naira.bank_name}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Account Name</p>
                          <p className="font-medium text-gray-900">{paymentDetails.naira.account_name}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Account Number</p>
                          <p className="font-medium text-gray-900">{paymentDetails.naira.account_number}</p>
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        Contact support if you need to update these details
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                  <div className="flex items-start gap-3">
                    <Building2 className="h-5 w-5 text-amber-600 mt-1" />
                    <div>
                      <p className="text-sm font-medium text-amber-900">NAIRA Bank Account Not Set</p>
                      <p className="text-xs text-amber-700 mt-1">
                        Go to <a href="/setup" className="underline">Setup</a> to view or add your bank details
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* USDT Wallet Address */}
              {paymentDetails.usdt ? (
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <div className="flex items-start gap-3">
                    <Wallet className="h-5 w-5 text-gray-600 mt-1" />
                    <div className="flex-1 space-y-2">
                      <p className="text-sm font-medium text-gray-900">USDT Wallet Address (BEP20)</p>
                      <p className="font-mono text-sm text-gray-900 break-all">
                        {paymentDetails.usdt}
                      </p>
                      <p className="text-xs text-gray-500 mt-2">
                        Contact support if you need to update this address
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                  <div className="flex items-start gap-3">
                    <Wallet className="h-5 w-5 text-amber-600 mt-1" />
                    <div>
                      <p className="text-sm font-medium text-amber-900">USDT Wallet Not Set</p>
                      <p className="text-xs text-amber-700 mt-1">
                        Go to <a href="/setup" className="underline">Setup</a> to view or add your USDT wallet address
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Referral Codes */}
      <Card className="border-emerald-200 bg-emerald-50">
        <CardHeader>
          <CardTitle className="text-emerald-900">Referral Codes</CardTitle>
          <CardDescription className="text-emerald-700">
            Share your referral codes to earn bonuses
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {nairaWallet && (
            <div className="rounded-lg bg-white p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-700">NAIRA Wallet</p>
                  <p className="text-lg font-mono font-bold text-emerald-700">
                    {nairaWallet.referral_code}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopyReferralCode(nairaWallet.referral_code)}
                >
                  {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          )}

          {usdtWallet && (
            <div className="rounded-lg bg-white p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-700">USDT Wallet</p>
                  <p className="text-lg font-mono font-bold text-emerald-700">
                    {usdtWallet.referral_code}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopyReferralCode(usdtWallet.referral_code)}
                >
                  {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          )}

          <div className="text-sm text-emerald-900">
            <p className="font-medium">How it works:</p>
            <ul className="mt-2 list-inside list-disc space-y-1 text-emerald-800">
              <li>Share your referral code with friends</li>
              <li>They use it when registering</li>
              <li>You earn 5% bonus when they place their first bet</li>
              <li>Both you and your friend benefit!</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Account Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Account Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-600">NAIRA Wallet Status</p>
              <p className={`mt-1 text-lg font-semibold ${nairaWallet?.is_blocked ? 'text-red-600' : 'text-green-600'}`}>
                {nairaWallet?.is_blocked ? 'Blocked' : 'Active'}
              </p>
            </div>

            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-600">USDT Wallet Status</p>
              <p className={`mt-1 text-lg font-semibold ${usdtWallet?.is_blocked ? 'text-red-600' : 'text-green-600'}`}>
                {usdtWallet?.is_blocked ? 'Blocked' : 'Active'}
              </p>
            </div>

            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-600">Account Type</p>
              <p className="mt-1 text-lg font-semibold text-gray-900">
                {user?.is_admin ? 'Admin' : 'User'}
              </p>
            </div>

            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-600">Verification Status</p>
              <p className="mt-1 text-lg font-semibold text-gray-900">
                Verified
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Security - Password Change */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Security</CardTitle>
              <CardDescription>
                Manage your password and security settings
              </CardDescription>
            </div>
            {!changingPassword && (
              <Button variant="outline" size="sm" onClick={() => setChangingPassword(true)}>
                Change Password
              </Button>
            )}
          </div>
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

          {changingPassword ? (
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="currentPassword">Current Password</Label>
                <Input
                  id="currentPassword"
                  name="currentPassword"
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={handlePasswordChange}
                  disabled={loading}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="newPassword">New Password</Label>
                <Input
                  id="newPassword"
                  name="newPassword"
                  type="password"
                  value={passwordData.newPassword}
                  onChange={handlePasswordChange}
                  disabled={loading}
                  required
                  minLength={8}
                />
                <p className="text-xs text-gray-500">
                  Must be at least 8 characters long
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={handlePasswordChange}
                  disabled={loading}
                  required
                />
              </div>

              <div className="flex gap-3">
                <Button type="submit" disabled={loading}>
                  {loading ? 'Changing...' : 'Change Password'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCancelPasswordChange}
                  disabled={loading}
                >
                  Cancel
                </Button>
              </div>
            </form>
          ) : (
            <p className="text-sm text-gray-600">
              Click &quot;Change Password&quot; to update your account password
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

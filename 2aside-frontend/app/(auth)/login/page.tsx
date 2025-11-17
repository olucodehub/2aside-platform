'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { authService, walletService, handleApiError } from '@/lib/api'
import { useAuthStore, useWalletStore } from '@/lib/store'

export default function LoginPage() {
  const router = useRouter()
  const login = useAuthStore((state) => state.login)
  const { selectedCurrency, setNairaWallet, setUsdtWallet } = useWalletStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await authService.login(email, password)
      const { access_token, user } = response.data

      // Store in Zustand and localStorage
      login(access_token, user)

      // Fetch wallet data to check if setup is needed
      try {
        const nairaResponse = await walletService.getWallet('NAIRA')
        const usdtResponse = await walletService.getWallet('USDT')

        const nairaWallet = nairaResponse.data.data?.wallet || null
        const usdtWallet = usdtResponse.data.data?.wallet || null

        setNairaWallet(nairaWallet)
        setUsdtWallet(usdtWallet)

        // Check if user needs to set up payment method for the selected currency
        const needsNairaSetup = selectedCurrency === 'NAIRA' && !nairaWallet?.bank_details_id
        const needsUsdtSetup = selectedCurrency === 'USDT' && !usdtWallet?.wallet_address

        if (needsNairaSetup) {
          router.push('/setup?currency=NAIRA')
        } else if (needsUsdtSetup) {
          router.push('/setup?currency=USDT')
        } else {
          router.push('/dashboard')
        }
      } catch (walletErr) {
        // If wallet fetch fails, still redirect to dashboard
        console.error('Failed to fetch wallets:', walletErr)
        router.push('/dashboard')
      }
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Welcome back</CardTitle>
        <CardDescription>
          Sign in to your 2-Aside account
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </Button>

          <div className="text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <Link href="/register" className="font-medium text-emerald-600 hover:text-emerald-700">
              Sign up
            </Link>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

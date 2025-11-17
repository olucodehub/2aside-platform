'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Wallet, TrendingUp, History, User, LogOut, Shield, Users, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/lib/store'
import { Button } from '@/components/ui/button'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'My Requests', href: '/dashboard/funding/status', icon: FileText },
  { name: 'Active Matches', href: '/dashboard/matches', icon: Users },
  { name: 'Wallet', href: '/dashboard/wallet', icon: Wallet },
  { name: 'Games', href: '/dashboard/games', icon: TrendingUp },
  { name: 'History', href: '/dashboard/history', icon: History },
  { name: 'Profile', href: '/dashboard/profile', icon: User },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <div className="flex h-full w-64 flex-col bg-white border-r border-gray-200">
      {/* Logo */}
      <div className="flex h-16 items-center px-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold text-emerald-600">2-Aside</h1>
      </div>

      {/* User info */}
      <div className="px-6 py-4 border-b border-gray-200">
        <p className="text-sm font-medium text-gray-900">{user?.username || 'User'}</p>
        <p className="text-xs text-gray-500">{user?.email}</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          )
        })}

        {/* Admin Link - Only show for admin users */}
        {user?.is_admin && (
          <>
            <div className="my-2 border-t border-gray-200"></div>
            <Link
              href="/admin"
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                pathname?.startsWith('/admin')
                  ? 'bg-purple-50 text-purple-700'
                  : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              <Shield className="h-5 w-5" />
              Admin Portal
            </Link>
          </>
        )}
      </nav>

      {/* Logout */}
      <div className="p-3 border-t border-gray-200">
        <Button
          variant="ghost"
          className="w-full justify-start text-red-600 hover:bg-red-50 hover:text-red-700"
          onClick={handleLogout}
        >
          <LogOut className="mr-3 h-5 w-5" />
          Logout
        </Button>
      </div>
    </div>
  )
}

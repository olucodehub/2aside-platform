'use client'

import { useAuthStore } from '@/lib/store'

export default function DebugPage() {
  const { user, token, isAuthenticated } = useAuthStore()

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Debug Page - Auth Store</h1>

      <div className="space-y-4">
        <div className="border rounded-lg p-4 bg-white">
          <h2 className="text-xl font-semibold mb-2">Authentication Status</h2>
          <p className="text-lg">
            Is Authenticated: <span className={isAuthenticated ? 'text-green-600' : 'text-red-600'}>
              {isAuthenticated ? 'YES' : 'NO'}
            </span>
          </p>
        </div>

        <div className="border rounded-lg p-4 bg-white">
          <h2 className="text-xl font-semibold mb-2">User Data</h2>
          {user ? (
            <div className="space-y-2">
              <p><strong>ID:</strong> {user.id}</p>
              <p><strong>Email:</strong> {user.email}</p>
              <p><strong>Username:</strong> {user.username}</p>
              <p><strong>Phone:</strong> {user.phone}</p>
              <p className="text-lg">
                <strong>Is Admin:</strong> <span className={user.is_admin ? 'text-green-600 font-bold' : 'text-red-600'}>
                  {user.is_admin ? 'YES ✅' : 'NO ❌'}
                </span>
              </p>
            </div>
          ) : (
            <p className="text-red-600">No user data found</p>
          )}
        </div>

        <div className="border rounded-lg p-4 bg-white">
          <h2 className="text-xl font-semibold mb-2">Token</h2>
          {token ? (
            <p className="break-all text-sm">{token}</p>
          ) : (
            <p className="text-red-600">No token found</p>
          )}
        </div>

        <div className="border rounded-lg p-4 bg-white">
          <h2 className="text-xl font-semibold mb-2">Full User Object (JSON)</h2>
          <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm">
            {JSON.stringify(user, null, 2)}
          </pre>
        </div>

        <div className="border rounded-lg p-4 bg-yellow-50">
          <h2 className="text-xl font-semibold mb-2">Instructions</h2>
          <ol className="list-decimal list-inside space-y-2">
            <li>If <strong>Is Admin</strong> shows <span className="text-red-600">NO ❌</span>, you need to logout and login again</li>
            <li>Make sure your database has <code className="bg-gray-200 px-1">is_admin = 1</code> for your user</li>
            <li>Make sure the auth service has been restarted with the updated code</li>
            <li>Clear browser localStorage and login again</li>
          </ol>
        </div>
      </div>
    </div>
  )
}

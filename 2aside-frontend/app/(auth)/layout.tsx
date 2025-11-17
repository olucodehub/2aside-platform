export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50">
      <div className="flex min-h-screen items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
        <div className="w-full max-w-md space-y-8">
          {/* Logo */}
          <div className="text-center">
            <h1 className="text-4xl font-bold text-emerald-600">2-Aside</h1>
            <p className="mt-2 text-sm text-gray-600">
              P2P Betting Platform
            </p>
          </div>

          {children}
        </div>
      </div>
    </div>
  )
}

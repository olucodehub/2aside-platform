'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  // Log error to console but don't show overlay
  console.error('Application error:', error)

  return null // Return null to prevent any error UI from showing
}

'use client'

import { useState, useEffect } from 'react'
import { Clock } from 'lucide-react'
import { Card } from '@/components/ui/card'

export default function NextMergeCycleCountdown() {
  const [timeUntilNextMerge, setTimeUntilNextMerge] = useState('')
  const [nextMergeTime, setNextMergeTime] = useState('')

  const calculateTimeUntilNextMerge = () => {
    // Get current time in WAT timezone (Africa/Lagos = UTC+1)
    const now = new Date()

    // Use Intl API to get time in WAT timezone
    const watTime = new Date(now.toLocaleString('en-US', { timeZone: 'Africa/Lagos' }))

    const currentHour = watTime.getHours()
    const currentMinute = watTime.getMinutes()
    const currentSecond = watTime.getSeconds()

    // Merge times in WAT: 9am, 3pm (15:00), 9pm (21:00)
    const mergeTimes = [9, 15, 21]

    let nextMergeHour = mergeTimes.find(hour => hour > currentHour) || mergeTimes[0]
    let daysToAdd = 0

    // If all merge times today have passed, next merge is tomorrow at 9am
    if (nextMergeHour <= currentHour || (nextMergeHour === currentHour && currentMinute >= 0)) {
      if (mergeTimes.every(hour => hour <= currentHour)) {
        nextMergeHour = mergeTimes[0]
        daysToAdd = 1
      }
    }

    // Calculate next merge date/time in WAT
    const nextMerge = new Date(watTime)
    nextMerge.setDate(watTime.getDate() + daysToAdd)
    nextMerge.setHours(nextMergeHour, 0, 0, 0)

    // Calculate time difference
    const diff = nextMerge.getTime() - watTime.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    const seconds = Math.floor((diff % (1000 * 60)) / 1000)

    // Format countdown
    let countdown = ''
    if (hours > 0) {
      countdown = `${hours}h ${minutes}m ${seconds}s`
    } else if (minutes > 0) {
      countdown = `${minutes}m ${seconds}s`
    } else {
      countdown = `${seconds}s`
    }

    // Format next merge time
    const period = nextMergeHour >= 12 ? 'PM' : 'AM'
    const displayHour = nextMergeHour > 12 ? nextMergeHour - 12 : nextMergeHour === 0 ? 12 : nextMergeHour
    const nextMergeFormatted = `${displayHour}:00 ${period} WAT${daysToAdd > 0 ? ' (Tomorrow)' : ''}`

    setTimeUntilNextMerge(countdown)
    setNextMergeTime(nextMergeFormatted)
  }

  useEffect(() => {
    // Calculate immediately
    calculateTimeUntilNextMerge()

    // Update every second
    const interval = setInterval(calculateTimeUntilNextMerge, 1000)

    return () => clearInterval(interval)
  }, [])

  return (
    <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
            <Clock className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Next Merge Cycle</h3>
            <p className="text-xs text-gray-600">{nextMergeTime}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold font-mono text-blue-600">
            {timeUntilNextMerge}
          </div>
          <p className="text-xs text-gray-500">Time remaining</p>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-blue-200">
        <p className="text-xs text-gray-600">
          Merge cycles run at <strong className="text-blue-700">9:00 AM</strong>, <strong className="text-blue-700">3:00 PM</strong>, and <strong className="text-blue-700">9:00 PM</strong> WAT daily.
          Fund or withdraw requests are matched during these times.
        </p>
      </div>
    </Card>
  )
}

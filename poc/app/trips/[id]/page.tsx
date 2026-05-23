'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import type { Trip, TripData, Day } from '@/lib/types'
import DayTabs from '@/components/trip/DayTabs'
import StopCard from '@/components/trip/StopCard'
import NavigateButton from '@/components/trip/NavigateButton'

export default function TripViewPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [trip, setTrip] = useState<Trip | null>(null)
  const [tripData, setTripData] = useState<TripData | null>(null)
  const [activeDay, setActiveDay] = useState(0)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [generateLog, setGenerateLog] = useState('')
  const [error, setError] = useState('')
  const startedRef = useRef(false)

  async function loadTrip() {
    const res = await fetch(`/api/trips/${id}`)
    if (!res.ok) { if (res.status === 404) router.push('/trips'); return }
    const data = await res.json()
    setTrip(data.trip); setTripData(data.tripData); setLoading(false)
    return data.trip
  }

  async function startGeneration() {
    setGenerating(true); setGenerateLog('Starting…'); setError('')
    const res = await fetch(`/api/trips/${id}/generate`, { method: 'POST' })
    if (!res.ok || !res.body) { setError('Failed to start generation'); setGenerating(false); return }
    const reader = res.body.getReader(); const decoder = new TextDecoder(); let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n'); buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const payload = line.slice(6)
          if (payload === '[DONE]') { setGenerating(false); loadTrip(); return }
          try {
            const evt = JSON.parse(payload)
            if (evt.type === 'progress') setGenerateLog(evt.message)
            if (evt.type === 'error') { setError(evt.message); setGenerating(false); return }
          } catch { /* partial chunk */ }
        }
      }
    }
    setGenerating(false); loadTrip()
  }

  useEffect(() => {
    loadTrip().then(t => { if (t?.status === 'draft' && !startedRef.current) { startedRef.current = true; startGeneration() } })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center"><div className="text-4xl mb-3 animate-pulse">🗺️</div><p className="text-gray-500 text-sm">Loading trip…</p></div>
    </div>
  )
  if (!trip) return null
  const days: Day[] = tripData?.days || []
  const currentDay = days[activeDay]

  if (generating || trip.status === 'generating') return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="bg-gradient-to-b from-brand-900 to-brand-700 px-6 pt-14 pb-6">
        <div className="flex items-center gap-3">
          <Link href="/trips" className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          </Link>
          <h1 className="text-white text-xl font-bold truncate">{trip.title}</h1>
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="text-center">
          <div className="text-6xl mb-6 animate-bounce">✨</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Building your trip…</h2>
          <p className="text-gray-500 text-sm mb-4">Claude is planning your itinerary</p>
          {generateLog && <div className="bg-brand-50 border border-brand-100 rounded-xl p-3 text-sm text-brand-700 max-w-xs mx-auto">{generateLog}</div>}
          {error && <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700 mt-3 max-w-xs mx-auto">{error}</div>}
        </div>
      </div>
    </div>
  )

  if (trip.status === 'error') return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="bg-gradient-to-b from-brand-900 to-brand-700 px-6 pt-14 pb-6">
        <div className="flex items-center gap-3">
          <Link href="/trips" className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          </Link>
          <h1 className="text-white text-xl font-bold truncate">{trip.title}</h1>
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Generation failed</h2>
          <p className="text-gray-500 text-sm mb-6">Something went wrong. Please try again.</p>
          <button onClick={() => { startedRef.current = false; startGeneration() }} className="btn-primary">Retry</button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-gradient-to-b from-brand-900 to-brand-700 px-6 pt-14 pb-0">
        <div className="flex items-center gap-3 pb-4">
          <Link href="/trips" className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center active:bg-white/20 flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          </Link>
          <div className="flex-1 min-w-0">
            <h1 className="text-white text-xl font-bold truncate">{trip.title}</h1>
            {tripData?.summary && <p className="text-brand-200 text-xs mt-0.5 line-clamp-1">{tripData.summary}</p>}
          </div>
          <Link href={`/trips/${id}/settings`} className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center active:bg-white/20 flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
          </Link>
        </div>
        {tripData && (
          <div className="flex gap-4 pb-4">
            {tripData.total_days && <div className="text-center"><p className="text-white font-bold text-lg leading-none">{tripData.total_days}</p><p className="text-brand-300 text-xs mt-0.5">days</p></div>}
            {tripData.total_distance_km && (<><div className="w-px bg-brand-700" /><div className="text-center"><p className="text-white font-bold text-lg leading-none">{tripData.total_distance_km}</p><p className="text-brand-300 text-xs mt-0.5">km</p></div></>)}
            {tripData.total_stops && (<><div className="w-px bg-brand-700" /><div className="text-center"><p className="text-white font-bold text-lg leading-none">{tripData.total_stops}</p><p className="text-brand-300 text-xs mt-0.5">stops</p></div></>)}
          </div>
        )}
        {days.length > 0 && (
          <div className="-mx-6"><DayTabs days={days} activeIndex={activeDay} onSelect={setActiveDay} /></div>
        )}
      </div>
      {currentDay ? (
        <div className="px-4 pt-4 pb-32 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-bold text-gray-900">Day {currentDay.day_number}{currentDay.title ? ` — ${currentDay.title}` : ''}</h2>
              {currentDay.overnight_location && <p className="text-sm text-gray-500 mt-0.5">🌙 Overnight: {currentDay.overnight_location}</p>}
            </div>
            {currentDay.stops && currentDay.stops.length > 0 && (
              <NavigateButton destination={(currentDay.stops[currentDay.stops.length - 1]?.address || currentDay.overnight_location || '')} label="Full route" compact />
            )}
          </div>
          {(currentDay.stops || []).map((stop, i) => <StopCard key={i} stop={stop} index={i} />)}
          {currentDay.eating && currentDay.eating.length > 0 && (
            <section>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2 px-1">🍽️ Eating</h3>
              <div className="space-y-2">
                {currentDay.eating.map((place, i) => (
                  <div key={i} className="card">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-gray-900 text-sm">{place.name}</p>
                        <p className="text-xs text-gray-500 capitalize">{place.meal_type}</p>
                        {place.description && <p className="text-sm text-gray-600 mt-1">{place.description}</p>}
                        {place.address && <p className="text-xs text-gray-400 mt-0.5 truncate">📍 {place.address}</p>}
                      </div>
                      {place.address && <NavigateButton destination={place.address} compact />}
                    </div>
                    {place.booking_required && <p className="text-xs text-amber-600 font-medium mt-2">⚠️ Booking recommended</p>}
                  </div>
                ))}
              </div>
            </section>
          )}
          {currentDay.notes && (
            <div className="bg-amber-50 border border-amber-100 rounded-2xl p-4">
              <p className="text-xs font-semibold text-amber-700 mb-1">💡 Tips for today</p>
              <p className="text-sm text-amber-800">{currentDay.notes}</p>
            </div>
          )}
          <div className="flex gap-3 pt-2">
            {activeDay > 0 && <button onClick={() => setActiveDay(activeDay - 1)} className="btn-secondary flex-1">← Day {activeDay}</button>}
            {activeDay < days.length - 1 && <button onClick={() => setActiveDay(activeDay + 1)} className="btn-primary flex-1">Day {activeDay + 2} →</button>}
          </div>
        </div>
      ) : (
        <div className="px-4 pt-12 text-center text-gray-400"><p>No days planned yet</p></div>
      )}
    </div>
  )
}

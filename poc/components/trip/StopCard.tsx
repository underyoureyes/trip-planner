'use client'

import { useState } from 'react'
import type { Stop } from '@/lib/types'
import { STOP_TYPE_ICONS } from '@/lib/navigation'
import NavigateButton from './NavigateButton'

interface Props { stop: Stop; index: number }

export default function StopCard({ stop, index }: Props) {
  const [expanded, setExpanded] = useState(false)
  const icon = STOP_TYPE_ICONS[stop.type] || '📍'
  const hasDetail = !!(stop.description || stop.booking_ref || stop.address || stop.phone || stop.website || stop.notes)
  const needsNavigation = stop.type !== 'drive'

  return (
    <div className="card overflow-hidden">
      <div className="flex items-start gap-3 cursor-pointer" onClick={() => hasDetail && setExpanded(!expanded)}>
        <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center text-xl">{icon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-400">{index + 1}.</span>
            <h3 className="font-semibold text-gray-900 truncate">{stop.name}</h3>
          </div>
          {stop.type === 'drive' && stop.drive_time_mins && (
            <p className="text-sm text-gray-500 mt-0.5">🚗 {Math.floor(stop.drive_time_mins / 60)}h {stop.drive_time_mins % 60}m{stop.distance_km ? ` · ${stop.distance_km} km` : ''}</p>
          )}
          {stop.type !== 'drive' && stop.duration_mins && (
            <p className="text-sm text-gray-500 mt-0.5">⏱️ {stop.duration_mins < 60 ? `${stop.duration_mins}m` : `${Math.floor(stop.duration_mins / 60)}h ${stop.duration_mins % 60}m`}</p>
          )}
          {stop.type === 'hotel' && stop.check_in && (
            <p className="text-xs text-gray-400 mt-0.5">Check-in: {stop.check_in} · Check-out: {stop.check_out}</p>
          )}
        </div>
        {hasDetail && (
          <svg className={`w-4 h-4 text-gray-400 flex-shrink-0 mt-1 transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </div>
      {expanded && hasDetail && (
        <div className="mt-3 pt-3 border-t border-gray-100 space-y-3">
          {stop.description && <p className="text-sm text-gray-600">{stop.description}</p>}
          <div className="space-y-2">
            {stop.address && <div className="flex items-start gap-2"><span className="text-gray-400 text-sm">📍</span><span className="text-sm text-gray-700">{stop.address}</span></div>}
            {stop.phone && <div className="flex items-start gap-2"><span className="text-gray-400 text-sm">📞</span><a href={`tel:${stop.phone}`} className="text-sm text-brand-600">{stop.phone}</a></div>}
            {stop.website && <div className="flex items-start gap-2"><span className="text-gray-400 text-sm">🔗</span><a href={stop.website} target="_blank" rel="noopener noreferrer" className="text-sm text-brand-600 truncate">{stop.website.replace(/^https?:\/\//, '')}</a></div>}
            {stop.booking_ref && <div className="flex items-start gap-2"><span className="text-gray-400 text-sm">🏾️</span><span className="text-sm text-gray-700 font-mono">{stop.booking_ref}</span></div>}
          </div>
          {stop.notes && <div className="bg-amber-50 rounded-xl p-3"><p className="text-xs font-semibold text-amber-700 mb-1">Notes</p><p className="text-sm text-amber-800">{stop.notes}</p></div>}
          {needsNavigation && <NavigateButton destination={stop.address || stop.name} label="Navigate here" />}
        </div>
      )}
    </div>
  )
}

'use client'

import { useState } from 'react'
import { buildNavigateUrl } from '@/lib/navigation'

interface Props {
  destination: string
  label?: string
  compact?: boolean
}

export default function NavigateButton({ destination, label, compact = false }: Props) {
  const [showOptions, setShowOptions] = useState(false)
  const urls = buildNavigateUrl(destination)

  if (compact) return (
    <a href={urls.google} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-600 text-white text-xs font-semibold rounded-lg active:bg-brand-700 no-underline">
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      Navigate
    </a>
  )

  return (
    <div className="relative">
      <button onClick={() => setShowOptions(!showOptions)}
        className="flex items-center gap-2 px-4 py-2.5 bg-brand-600 text-white text-sm font-semibold rounded-xl active:bg-brand-700 w-full justify-center">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        {label || `Navigate to ${destination}`}
      </button>
      {showOptions && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setShowOptions(false)} />
          <div className="absolute bottom-full mb-2 left-0 right-0 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden z-50">
            <div className="px-4 py-3 border-b border-gray-100">
              <p className="text-xs text-gray-500 font-medium">Open in…</p>
              <p className="text-sm font-semibold text-gray-900 truncate mt-0.5">{destination}</p>
            </div>
            <a href={urls.google} className="flex items-center gap-3 px-4 py-3.5 active:bg-gray-50 no-underline border-b border-gray-100" onClick={() => setShowOptions(false)}>
              <span className="text-xl">🗺️</span>
              <div><p className="text-sm font-semibold text-gray-900">Google Maps</p><p className="text-xs text-gray-500">Opens app if installed</p></div>
            </a>
            <a href={urls.apple} className="flex items-center gap-3 px-4 py-3.5 active:bg-gray-50 no-underline border-b border-gray-100" onClick={() => setShowOptions(false)}>
              <span className="text-xl">🍎</span>
              <div><p className="text-sm font-semibold text-gray-900">Apple Maps</p><p className="text-xs text-gray-500">Built-in iPhone maps</p></div>
            </a>
            <a href={urls.web} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 px-4 py-3.5 active:bg-gray-50 no-underline" onClick={() => setShowOptions(false)}>
              <span className="text-xl">🌐</span>
              <div><p className="text-sm font-semibold text-gray-900">Google Maps (web)</p><p className="text-xs text-gray-500">Opens in browser</p></div>
            </a>
          </div>
        </>
      )}
    </div>
  )
}

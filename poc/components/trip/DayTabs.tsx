'use client'

import { useRef, useEffect } from 'react'
import type { Day } from '@/lib/types'

interface Props {
  days: Day[]
  activeIndex: number
  onSelect: (index: number) => void
}

export default function DayTabs({ days, activeIndex, onSelect }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const activeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (activeRef.current && scrollRef.current) {
      activeRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
    }
  }, [activeIndex])

  function formatTabDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
  }

  return (
    <div ref={scrollRef} className="flex gap-2 overflow-x-auto px-4 py-3 scrollbar-none" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
      {days.map((day, i) => {
        const isActive = i === activeIndex
        return (
          <button key={i} ref={isActive ? activeRef : undefined} onClick={() => onSelect(i)}
            className={`flex-shrink-0 px-4 py-2 rounded-xl text-sm font-medium transition-colors whitespace-nowrap ${
              isActive ? 'bg-brand-600 text-white shadow-sm' : 'bg-white text-gray-600 border border-gray-200'
            }`}>
            <span className="font-semibold">Day {day.day_number}</span>
            {day.date && <span className={`ml-1.5 text-xs ${isActive ? 'text-brand-200' : 'text-gray-400'}`}>{formatTabDate(day.date)}</span>}
          </button>
        )
      })}
    </div>
  )
}

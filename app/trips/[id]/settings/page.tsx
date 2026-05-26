'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'

export default function TripSettingsPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [title, setTitle] = useState('')
  const [isShared, setIsShared] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetch(`/api/trips/${id}`).then(r => r.json()).then(data => {
      setTitle(data.trip?.title || '')
      setIsShared(data.trip?.is_shared || false)
      setLoading(false)
    })
  }, [id])

  async function save() {
    setSaving(true); setError(''); setMessage('')
    const res = await fetch(`/api/trips/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, is_shared: isShared }) })
    if (!res.ok) { const json = await res.json().catch(() => ({})); setError(json.error || 'Save failed') }
    else { setMessage('Saved!') }
    setSaving(false)
  }

  async function deleteTrip() {
    if (!confirm('Delete this trip? This cannot be undone.')) return
    setDeleting(true)
    await fetch(`/api/trips/${id}`, { method: 'DELETE' })
    router.push('/trips')
  }

  if (loading) return <div className="min-h-screen bg-gray-50 flex items-center justify-center"><p className="text-gray-400 text-sm">Loading…</p></div>

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-gradient-to-b from-brand-900 to-brand-700 px-6 pt-14 pb-6">
        <div className="flex items-center gap-3">
          <Link href={`/trips/${id}`} className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center active:bg-white/20">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          </Link>
          <h1 className="text-white text-xl font-bold">Trip settings</h1>
        </div>
      </div>

      <div className="px-4 pt-6 pb-32 space-y-5">
        <div className="card space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Trip name</label>
            <input type="text" value={title} onChange={e => setTitle(e.target.value)} className="input-field" />
          </div>
          <div>
            <label className="flex items-center justify-between cursor-pointer">
              <div>
                <p className="text-sm font-medium text-gray-700">Share with all users</p>
                <p className="text-xs text-gray-400 mt-0.5">Others can view but not edit this trip</p>
              </div>
              <div onClick={() => setIsShared(!isShared)}
                className={`relative w-12 h-6 rounded-full transition-colors flex-shrink-0 ${isShared ? 'bg-brand-600' : 'bg-gray-300'}`}>
                <div className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${isShared ? 'translate-x-6' : ''}`} />
              </div>
            </label>
          </div>
        </div>

        {message && <div className="bg-green-50 border border-green-200 rounded-xl p-3 text-sm text-green-700">{message}</div>}
        {error && <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">{error}</div>}

        <button onClick={save} disabled={saving} className="btn-primary disabled:opacity-50">{saving ? 'Saving…' : 'Save'}</button>

        <div className="pt-4">
          <button onClick={deleteTrip} disabled={deleting} className="w-full py-3 text-red-500 font-medium text-sm disabled:opacity-50">
            {deleting ? 'Deleting…' : 'Delete trip'}
          </button>
        </div>
      </div>
    </div>
  )
}

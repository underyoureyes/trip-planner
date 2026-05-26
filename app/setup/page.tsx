'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'

type Step = 'profile' | 'apikey' | 'prefs' | 'done'

export default function SetupPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>('profile')

  const [homeTown, setHomeTown] = useState('')
  const [vehicleName, setVehicleName] = useState('')
  const [vehicleType, setVehicleType] = useState<'car' | 'campervan' | 'motorhome' | 'motorcycle'>('car')

  const [apiKey, setApiKey] = useState('')
  const [skipApiKey, setSkipApiKey] = useState(false)
  const [validating, setValidating] = useState(false)
  const [apiKeyError, setApiKeyError] = useState('')

  const [units, setUnits] = useState<'metric' | 'imperial'>('metric')
  const [currency, setCurrency] = useState('GBP')

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const steps: Step[] = ['profile', 'apikey', 'prefs']
  const stepIndex = steps.indexOf(step)
  const progress = step === 'done' ? 100 : ((stepIndex + 1) / steps.length) * 100

  async function validateAndNextFromApiKey() {
    if (skipApiKey) { setStep('prefs'); return }
    if (!apiKey.trim()) { setApiKeyError('Enter your API key or choose "skip"'); return }
    if (!apiKey.startsWith('sk-ant-')) { setApiKeyError('Claude API keys start with sk-ant-'); return }
    setValidating(true)
    setApiKeyError('')
    try {
      const res = await fetch('/api/settings/validate-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey }),
      })
      const json = await res.json()
      if (!json.valid) { setApiKeyError('Key rejected by Claude — double-check it'); setValidating(false); return }
    } catch {
      setApiKeyError('Could not validate key — check your connection')
      setValidating(false)
      return
    }
    setValidating(false)
    setStep('prefs')
  }

  async function finish() {
    setSaving(true)
    setError('')
    const supabase = createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) { router.push('/login'); return }

    const { error: profileError } = await supabase
      .from('profiles')
      .upsert({ id: user.id, home_town: homeTown, vehicle_name: vehicleName || null, vehicle_type: vehicleType, setup_complete: true })

    if (profileError) { setError('Failed to save profile: ' + profileError.message); setSaving(false); return }

    const { error: settingsError } = await supabase
      .from('user_settings')
      .upsert({ user_id: user.id, claude_api_key: skipApiKey ? null : apiKey.trim(), distance_unit: units, currency })

    if (settingsError) { setError('Failed to save settings: ' + settingsError.message); setSaving(false); return }

    router.push('/trips')
    router.refresh()
  }

  if (step === 'done') return null

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-900 to-brand-700 flex flex-col">
      <div className="pt-12 pb-6 px-6 text-center">
        <div className="text-4xl mb-2">🗺️</div>
        <h1 className="text-white text-xl font-bold">Trip Planner</h1>
        <p className="text-brand-200 text-sm mt-1">Set up your account</p>
      </div>

      <div className="px-6 mb-2">
        <div className="h-1.5 bg-brand-800 rounded-full overflow-hidden">
          <div className="h-full bg-white rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
        </div>
        <p className="text-brand-300 text-xs mt-1.5 text-right">Step {stepIndex + 1} of {steps.length}</p>
      </div>

      <div className="flex-1 bg-gray-50 rounded-t-3xl px-6 pt-8 pb-safe">

        {step === 'profile' && (
          <>
            <h2 className="text-xl font-bold text-gray-900 mb-1">Your profile</h2>
            <p className="text-gray-500 text-sm mb-6">Tell us a bit about yourself</p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Home town <span className="text-gray-400 font-normal">(for route planning)</span></label>
                <input type="text" value={homeTown} onChange={e => setHomeTown(e.target.value)} className="input-field" placeholder="e.g. Manchester, UK" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Vehicle nickname <span className="text-gray-400 font-normal">(optional)</span></label>
                <input type="text" value={vehicleName} onChange={e => setVehicleName(e.target.value)} className="input-field" placeholder="e.g. The Blue Beast" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Vehicle type</label>
                <div className="grid grid-cols-2 gap-2">
                  {(['car', 'campervan', 'motorhome', 'motorcycle'] as const).map(v => (
                    <button key={v} type="button" onClick={() => setVehicleType(v)}
                      className={`py-3 px-4 rounded-xl border-2 text-sm font-medium transition-colors ${
                        vehicleType === v ? 'border-brand-500 bg-brand-50 text-brand-700' : 'border-gray-200 bg-white text-gray-700'
                      }`}>
                      {v === 'car' ? '🚗 Car' : v === 'campervan' ? '🚐 Campervan' : v === 'motorhome' ? '🏠 Motorhome' : '🏍️ Motorcycle'}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <button onClick={() => setStep('apikey')} className="btn-primary mt-8">Next</button>
          </>
        )}

        {step === 'apikey' && (
          <>
            <h2 className="text-xl font-bold text-gray-900 mb-1">Claude API key</h2>
            <p className="text-gray-500 text-sm mb-6">Needed to generate trips. Without it, you can view shared trips but not create new ones.</p>
            <div className="space-y-4">
              {!skipApiKey && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">API key</label>
                  <input type="password" value={apiKey} onChange={e => { setApiKey(e.target.value); setApiKeyError('') }}
                    className="input-field font-mono text-sm" placeholder="sk-ant-api03-…" autoComplete="off" spellCheck={false} />
                  <p className="text-xs text-gray-400 mt-1.5">Get yours at <a href="https://console.anthropic.com" target="_blank" rel="noopener noreferrer" className="text-brand-600 underline">console.anthropic.com</a></p>
                </div>
              )}
              {apiKeyError && <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">{apiKeyError}</div>}
              <label className="flex items-center gap-3 py-3 cursor-pointer">
                <input type="checkbox" checked={skipApiKey} onChange={e => { setSkipApiKey(e.target.checked); setApiKeyError('') }} className="w-5 h-5 rounded accent-brand-600" />
                <span className="text-sm text-gray-700">I don't have one — <span className="text-gray-500">read-only access</span></span>
              </label>
            </div>
            <div className="flex gap-3 mt-8">
              <button onClick={() => setStep('profile')} className="btn-secondary flex-1">Back</button>
              <button onClick={validateAndNextFromApiKey} disabled={validating} className="btn-primary flex-1 disabled:opacity-50">
                {validating ? 'Validating…' : 'Next'}
              </button>
            </div>
          </>
        )}

        {step === 'prefs' && (
          <>
            <h2 className="text-xl font-bold text-gray-900 mb-1">Preferences</h2>
            <p className="text-gray-500 text-sm mb-6">These can be changed later in settings</p>
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Distance units</label>
                <div className="flex gap-2">
                  {(['metric', 'imperial'] as const).map(u => (
                    <button key={u} type="button" onClick={() => setUnits(u)}
                      className={`flex-1 py-3 px-4 rounded-xl border-2 text-sm font-medium transition-colors ${
                        units === u ? 'border-brand-500 bg-brand-50 text-brand-700' : 'border-gray-200 bg-white text-gray-700'
                      }`}>
                      {u === 'metric' ? 'Kilometres (km)' : 'Miles (mi)'}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Currency</label>
                <select value={currency} onChange={e => setCurrency(e.target.value)} className="input-field bg-white">
                  <option value="GBP">🇬🇧 GBP — British Pound</option>
                  <option value="EUR">🇪🇺 EUR — Euro</option>
                  <option value="USD">🇺🇸 USD — US Dollar</option>
                  <option value="CAD">🇨🇦 CAD — Canadian Dollar</option>
                  <option value="AUD">🇦🇺 AUD — Australian Dollar</option>
                  <option value="CHF">🇨🇭 CHF — Swiss Franc</option>
                </select>
              </div>
            </div>
            {error && <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700 mt-4">{error}</div>}
            <div className="flex gap-3 mt-8">
              <button onClick={() => setStep('apikey')} className="btn-secondary flex-1">Back</button>
              <button onClick={finish} disabled={saving} className="btn-primary flex-1 disabled:opacity-50">
                {saving ? 'Saving…' : "Let's go!"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

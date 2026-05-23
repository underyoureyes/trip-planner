'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase'

export default function RegisterPage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (password.length < 10) { setError('Password must be at least 10 characters'); return }
    setLoading(true)

    const supabase = createClient()
    const { data: invite } = await supabase
      .from('invite_codes')
      .select('id, code, used_by, revoked, expires_at')
      .eq('code', inviteCode.toUpperCase().trim())
      .single()

    if (!invite) { setError('Invalid invite code'); setLoading(false); return }
    if (invite.used_by) { setError('This invite code has already been used'); setLoading(false); return }
    if (invite.revoked || new Date(invite.expires_at) < new Date()) {
      setError('This invite code has expired'); setLoading(false); return
    }

    const { data, error: signUpError } = await supabase.auth.signUp({
      email, password,
      options: { data: { name } },
    })

    if (signUpError || !data.user) {
      setError(signUpError?.message || 'Registration failed')
      setLoading(false); return
    }

    await supabase.from('invite_codes')
      .update({ used_by: data.user.id, used_at: new Date().toISOString() })
      .eq('code', inviteCode.toUpperCase().trim())

    router.push('/setup')
    router.refresh()
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-900 to-brand-700 flex flex-col">
      <div className="pt-16 pb-8 px-6 text-center">
        <div className="text-5xl mb-3">🗺️</div>
        <h1 className="text-white text-2xl font-bold">Trip Planner</h1>
        <p className="text-brand-200 mt-1 text-sm">Create your account</p>
      </div>
      <div className="flex-1 bg-gray-50 rounded-t-3xl px-6 pt-8 pb-safe">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Create account</h2>
        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Your name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)}
              className="input-field" placeholder="First name" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              className="input-field" placeholder="you@example.com" autoComplete="email" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Password <span className="text-gray-400 font-normal">(min 10 characters)</span>
            </label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              className="input-field" placeholder="••••••••••" autoComplete="new-password" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Invite code</label>
            <input type="text" value={inviteCode} onChange={e => setInviteCode(e.target.value)}
              className="input-field uppercase tracking-widest" placeholder="XXXXXXXX" required />
          </div>
          {error && <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">{error}</div>}
          <button type="submit" disabled={loading} className="btn-primary disabled:opacity-50">
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-500 mt-6">
          Already have an account?{' '}
          <Link href="/login" className="text-brand-600 font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  )
}

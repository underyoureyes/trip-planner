import { NextRequest, NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase-server'

export async function GET() {
  const supabase = await createServerSupabaseClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { data, error } = await supabase
    .from('user_settings')
    .select('distance_unit, currency, claude_api_key')
    .eq('user_id', user.id)
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  const maskedKey = data?.claude_api_key
    ? data.claude_api_key.slice(0, 14) + '…'
    : null

  return NextResponse.json({
    distance_unit: data?.distance_unit || 'metric',
    currency: data?.currency || 'GBP',
    has_api_key: !!data?.claude_api_key,
    api_key_hint: maskedKey,
  })
}

export async function PUT(request: NextRequest) {
  const supabase = await createServerSupabaseClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const body = await request.json()
  const update: Record<string, unknown> = { user_id: user.id }

  if (typeof body.distance_unit === 'string') {
    if (!['metric', 'imperial'].includes(body.distance_unit)) {
      return NextResponse.json({ error: 'Invalid distance_unit' }, { status: 400 })
    }
    update.distance_unit = body.distance_unit
  }

  if (typeof body.currency === 'string' && body.currency.length === 3) {
    update.currency = body.currency.toUpperCase()
  }

  if (typeof body.claude_api_key === 'string') {
    update.claude_api_key = body.claude_api_key.trim() || null
  }

  const { error } = await supabase
    .from('user_settings')
    .upsert(update, { onConflict: 'user_id' })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ ok: true })
}

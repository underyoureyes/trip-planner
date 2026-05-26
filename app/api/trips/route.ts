import { NextRequest, NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase-server'
import type { IntakeForm } from '@/lib/types'

export async function GET() {
  const supabase = await createServerSupabaseClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { data, error } = await supabase
    .from('trips')
    .select('id, title, status, start_date, end_date, is_shared, owner_id, created_at')
    .eq('owner_id', user.id)
    .order('created_at', { ascending: false })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

export async function POST(request: NextRequest) {
  const supabase = await createServerSupabaseClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { data: settings } = await supabase
    .from('user_settings')
    .select('claude_api_key')
    .eq('user_id', user.id)
    .single()

  if (!settings?.claude_api_key) {
    return NextResponse.json(
      { error: 'A Claude API key is required to create trips. Add one in settings.' },
      { status: 403 }
    )
  }

  let form: Partial<IntakeForm>
  try {
    form = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  if (!form.title?.trim()) return NextResponse.json({ error: 'Title required' }, { status: 400 })
  if (!form.origin?.trim()) return NextResponse.json({ error: 'Origin required' }, { status: 400 })
  if (!form.destination?.trim()) return NextResponse.json({ error: 'Destination required' }, { status: 400 })

  const { data: trip, error } = await supabase
    .from('trips')
    .insert({
      owner_id: user.id,
      title: form.title.trim(),
      status: 'draft',
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      is_shared: false,
      intake_form: form,
    })
    .select('id')
    .single()

  if (error || !trip) {
    return NextResponse.json({ error: error?.message || 'Insert failed' }, { status: 500 })
  }

  return NextResponse.json({ id: trip.id }, { status: 201 })
}

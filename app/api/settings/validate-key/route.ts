import { NextRequest, NextResponse } from 'next/server'
import { validateClaudeKey } from '@/lib/claude'

export async function POST(request: NextRequest) {
  let body: { apiKey?: string }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ valid: false, error: 'Invalid JSON' }, { status: 400 })
  }

  if (!body.apiKey || typeof body.apiKey !== 'string') {
    return NextResponse.json({ valid: false, error: 'apiKey required' }, { status: 400 })
  }

  const valid = await validateClaudeKey(body.apiKey.trim())
  return NextResponse.json({ valid })
}

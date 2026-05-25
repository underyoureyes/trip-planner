import Anthropic from '@anthropic-ai/sdk'
import type { IntakeForm, TripData } from './types'

export function getClaudeClient(apiKey: string) {
  return new Anthropic({ apiKey })
}

const SYSTEM_PROMPT = `You are an expert road trip planner specialising in UK and European road trips.
Generate a detailed, day-by-day itinerary as a single JSON object.

CRITICAL RULES:
- Output ONLY valid JSON — no markdown, no explanations, no code fences
- Follow the schema exactly — every field matters
- Every stop must include a real address or at minimum a town/region
- Balance driving and activities sensibly — respect the max_driving_hours constraint
- Realistic drive times (not Google Maps "no traffic" estimates)
- All website URLs must be real https:// links or null — no invented URLs
- Hotel stops MUST include check_in and check_out times matching the traveller's preferences
- Mark genuinely optional bonus stops with "suggested": true — these are extras the user may skip
- Required stops (hotel, fuel, must-visit places) must have "suggested": false or omit the field`

export function buildTripPrompt(form: IntakeForm): string {
  const startMs = new Date(form.start_date).getTime()
  const endMs = new Date(form.end_date).getTime()
  const days = Math.max(1, Math.ceil((endMs - startMs) / (1000 * 60 * 60 * 24)) + 1)
  const checkIn = form.preferred_check_in || '15:00'
  const checkOut = form.preferred_check_out || '10:00'

  return `Plan a ${days}-day road trip:

TITLE: ${form.title}
FROM: ${form.origin}
TO: ${form.destination}
DATES: ${form.start_date} to ${form.end_date} (${days} days)
TRAVELLERS: ${form.num_travellers}
INTERESTS: ${form.interests.length ? form.interests.join(', ') : 'general sightseeing'}
ACCOMMODATION: ${form.accommodation_style}
BUDGET: £${form.budget_per_day_gbp}/day per person
MAX DRIVING: ${form.driving_max_hours}h/day
PREFERRED CHECK-IN: ${checkIn} (use this for all hotel check_in fields)
PREFERRED CHECK-OUT: ${checkOut} (use this for all hotel check_out fields)
${form.must_include ? `MUST INCLUDE: ${form.must_include}` : ''}
${form.notes ? `NOTES: ${form.notes}` : ''}

For each day include:
- All driving legs as stops with type "drive"
- The hotel as a stop with type "hotel" including check_in and check_out
- 2-4 main activities (suggested: false)
- 1-2 optional bonus activities the user may skip (suggested: true)
- Eating suggestions for breakfast, lunch and dinner

Output exactly this JSON:
{
  "summary": "<one sentence>",
  "total_days": ${days},
  "total_distance_km": <number>,
  "total_stops": <number>,
  "days": [
    {
      "day_number": 1,
      "date": "${form.start_date}",
      "title": "<catchy title>",
      "overnight_location": "<town>",
      "stops": [
        {
          "name": "<name>",
          "type": "<drive|hotel|sightseeing|activity|viewpoint|town|cafe|pub|beach|nature|castle|distillery|museum|fuel|other>",
          "description": "<1-2 sentences>",
          "address": "<address or town, region>",
          "phone": null,
          "website": "<https:// url or null>",
          "duration_mins": <number, 0 for drives>,
          "suggested": <true for optional, false for required>,
          "drive_time_mins": <only for drives>,
          "distance_km": <only for drives>,
          "check_in": "<only for hotel, e.g. ${checkIn}>",
          "check_out": "<only for hotel, e.g. ${checkOut}>",
          "booking_ref": null,
          "notes": "<tip or null>"
        }
      ],
      "eating": [
        {
          "name": "<name>",
          "meal_type": "<breakfast|lunch|dinner|snack>",
          "description": "<brief>",
          "address": "<address>",
          "website": "<https:// or null>",
          "booking_required": false,
          "suggested": <true for optional>
        }
      ],
      "notes": "<day tips or null>"
    }
  ]
}`
}

export async function* streamTripGeneration(apiKey: string, form: IntakeForm): AsyncGenerator<string> {
  const client = getClaudeClient(apiKey)
  const stream = await client.messages.stream({
    model: 'claude-sonnet-4-6',
    max_tokens: 16000,
    system: SYSTEM_PROMPT,
    messages: [{ role: 'user', content: buildTripPrompt(form) }],
  })
  for await (const chunk of stream) {
    if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
      yield chunk.delta.text
    }
  }
}

export function parseTripJson(raw: string): TripData {
  const cleaned = raw.replace(/^```json\s*/i,'').replace(/^```\s*/i,'').replace(/```\s*$/i,'').trim()
  return JSON.parse(cleaned) as TripData
}

export async function validateClaudeKey(apiKey: string): Promise<boolean> {
  try {
    const client = getClaudeClient(apiKey)
    await client.messages.create({ model: 'claude-haiku-4-5-20251001', max_tokens: 10, messages: [{ role: 'user', content: 'Hi' }] })
    return true
  } catch { return false }
}

// Navigation deep-link builder
// Priority: Google Maps app → Apple Maps app → Google Maps web

export function buildNavigateUrl(destination: string): {
  google: string
  apple: string
  web: string
} {
  const encoded = encodeURIComponent(destination)
  return {
    google: `comgooglemaps://?daddr=${encoded}&directionsmode=driving`,
    apple: `maps://maps.apple.com/?daddr=${encoded}&dirflg=d`,
    web: `https://www.google.com/maps/dir/?api=1&destination=${encoded}&travelmode=driving`,
  }
}

export function buildRouteDayUrl(waypoints: string[]): {
  google: string
  apple: string
  web: string
} {
  if (waypoints.length === 0) return buildNavigateUrl('')
  const [start, ...rest] = waypoints
  const dest = rest[rest.length - 1] || start
  const vias = rest.slice(0, -1)

  const encodedDest = encodeURIComponent(dest)
  const googleWaypoints = waypoints.map(encodeURIComponent).join('+to:')
  const appleWaypoints = waypoints.map(encodeURIComponent).join('+to:')

  return {
    google: `comgooglemaps://?saddr=${encodeURIComponent(start)}&daddr=${googleWaypoints}&directionsmode=driving`,
    apple: `maps://maps.apple.com/?saddr=${encodeURIComponent(start)}&daddr=${appleWaypoints}`,
    web: `https://www.google.com/maps/dir/${waypoints.map(encodeURIComponent).join('/')}`,
  }
}

export function formatDriveTime(minutes: number): string {
  if (minutes < 60) return `${minutes} min`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

export const STOP_TYPE_ICONS: Record<string, string> = {
  sightseeing: '🏛️',
  dog_walk: '🐾',
  fuel: '⛽',
  golf: '⛳',
  distillery: '🥃',
  castle: '🏰',
  boat_trip: '⛵',
  cycling: '🚴',
  beach: '🏖️',
  restaurant: '🍽️',
  accommodation: '🛏️',
  activity: '🎯',
  viewpoint: '📸',
  town: '🏘️',
  other: '📍',
}

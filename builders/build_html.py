#!/usr/bin/env python3
"""Build trips/<trip-id>/output/index.html from trips/<trip-id>/data.json"""

import argparse, json, os, html
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── helpers ───────────────────────────────────────────────────────────────────
def h(s):
    return html.escape(str(s)) if s else ''

def fmt_date(date_str):
    d = datetime.strptime(date_str, '%Y-%m-%d')
    return d.strftime('%a %-d %b')

def maps_dir(waypoints):
    parts = '/'.join(w.replace(' ', '+') for w in waypoints)
    return f'https://www.google.com/maps/dir/{parts}'

def maps_search(query):
    return f'https://www.google.com/maps/search/?api=1&query={query.replace(" ", "+")}'

STOP_DOT = {
    'fuel': 'fuel', 'lunch_fuel': 'fuel', 'supplies': 'fuel',
    'tidal_warning': 'warn',
}
STOP_EMOJI = {
    'fuel':                  '⛽',
    'lunch_fuel':            '⛽',
    'dog_walk':              '🐾',
    'walk_dogs':             '🐾',
    'boat_dogs':             '⛴️',
    'cruise_dogs':           '🚢',
    'castle_dogs':           '🏰',
    'castle_dogs_optional':  '🏰',
    'sightseeing':           '📷',
    'sightseeing_dogs':      '📷',
    'photo_stop':            '📷',
    'supplies':              '🛒',
    'ebike_optional':        '🚲',
    'golf':                  '⛳',
    'distillery':            '🥃',
    'pub_dogs':              '🍺',
    'gondola_dogs':          '🚠',
    'train_dogs':            '🚂',
    'viewpoint':             '👁️',
    'attraction_dogs':       '🎭',
    'attraction_no_dogs':    '🎭',
    'afternoon_tea_no_dogs': '☕',
    'lunch_dogs':            '🍽️',
    'stop_dogs':             '🛍️',
    'museum_optional':       '🏛️',
    'tidal_warning':         '🌊',
}

FLAG_EMOJI = {
    'highlight': '⭐',
    'golf':      '⛳',
    'ebike':     '🚲',
    'train':     '🚂',
}

STAY_EMOJI = {
    'airbnb':      '🏡',
    'hotel':       '🏨',
    'booking_com': '🏡',
}

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
  :root {
    --ink:       #1a1a2e;
    --mist:      #e8edf5;
    --sky:       #2563a8;
    --sky-light: #dbeafe;
    --heather:   #6b4f7a;
    --gold:      #c9963a;
    --gold-pale: #fef3d0;
    --green:     #2d6a4f;
    --green-pale:#d8f3dc;
    --amber:     #e07b39;
    --amber-pale:#fff0e4;
    --slate:     #475569;
    --line:      #d1d9e6;
    --white:     #ffffff;
    --card-bg:   #f7f9fd;
    --radius:    14px;
    --shadow:    0 2px 16px rgba(26,26,46,0.10);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }

  body {
    font-family: 'Source Sans 3', sans-serif;
    background: var(--mist);
    color: var(--ink);
    font-size: 16px;
    line-height: 1.5;
    padding-bottom: 40px;
  }

  /* ── Hero ─────────────────────────────────────────────────── */
  .hero {
    background: linear-gradient(160deg, #1a1a2e 0%, #1e3a5f 55%, #2563a8 100%);
    padding: 52px 20px 36px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute; inset: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  }
  .hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 28px;
    color: #fff;
    letter-spacing: -0.5px;
    margin-bottom: 6px;
    position: relative;
  }
  .hero-sub {
    color: #93c5fd;
    font-size: 14px;
    font-weight: 300;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 20px;
    position: relative;
  }
  .hero-meta {
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
    position: relative;
  }
  .hero-chip {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 13px;
    color: #e0f2fe;
    backdrop-filter: blur(4px);
  }

  /* ── Nav tabs ─────────────────────────────────────────────── */
  .nav-wrap {
    background: var(--white);
    border-bottom: 1px solid var(--line);
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  }
  .nav-scroll {
    display: flex;
    overflow-x: auto;
    padding: 10px 12px;
    gap: 8px;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
  }
  .nav-scroll::-webkit-scrollbar { display: none; }
  .nav-btn {
    flex-shrink: 0;
    background: var(--mist);
    border: none;
    border-radius: 20px;
    padding: 7px 15px;
    font-family: 'Source Sans 3', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: var(--slate);
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
  }
  .nav-btn.active {
    background: var(--sky);
    color: var(--white);
    box-shadow: 0 2px 8px rgba(37,99,168,0.3);
  }

  /* ── Content ──────────────────────────────────────────────── */
  .content { padding: 16px; max-width: 560px; margin: 0 auto; }

  .day-section { display: none; }
  .day-section.active { display: block; }

  /* ── Day header card ──────────────────────────────────────── */
  .day-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563a8 100%);
    border-radius: var(--radius);
    padding: 20px;
    margin-bottom: 14px;
    box-shadow: var(--shadow);
    position: relative;
    overflow: hidden;
  }
  .day-header::after {
    content: '';
    position: absolute;
    right: -20px; top: -20px;
    width: 120px; height: 120px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
  }
  .day-number {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #93c5fd;
    margin-bottom: 4px;
  }
  .day-title {
    font-family: 'Playfair Display', serif;
    font-size: 20px;
    color: #fff;
    line-height: 1.25;
    margin-bottom: 12px;
  }
  .day-stats {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }
  .day-stat {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 13px;
    color: #bfdbfe;
  }
  .day-stat span { font-weight: 600; color: #fff; }
  .step-badge {
    padding: 2px 8px; border-radius: 99px; font-size: 11px;
    font-weight: 700; color: #fff; white-space: nowrap;
  }
  .step-badge.green { background: rgba(22,163,74,0.85); }
  .step-badge.amber { background: rgba(202,138,4,0.90); }
  .step-badge.red   { background: rgba(220,38,38,0.90); }

  /* ── Big map button ───────────────────────────────────────── */
  .map-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: var(--green);
    color: #fff;
    border-radius: var(--radius);
    padding: 16px 20px;
    text-decoration: none;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 14px;
    box-shadow: 0 3px 12px rgba(45,106,79,0.35);
    transition: transform 0.15s, box-shadow 0.15s;
    -webkit-touch-callout: none;
  }
  .map-btn:active { transform: scale(0.97); box-shadow: 0 1px 6px rgba(45,106,79,0.3); }
  .map-btn .map-icon { font-size: 22px; }
  .map-btn-text { line-height: 1.2; }
  .map-btn-text small { display: block; font-size: 12px; font-weight: 400; opacity: 0.85; margin-top: 1px; }

  /* ── Weather button ───────────────────────────────────────── */
  .weather-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    background: var(--sky-light);
    color: var(--sky);
    border: 1px solid rgba(37,99,168,0.2);
    border-radius: var(--radius);
    padding: 11px 16px;
    text-decoration: none;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 14px;
    transition: background 0.15s;
    -webkit-touch-callout: none;
  }
  .weather-btn:active { background: #bfdbfe; }

  /* ── Stops list ───────────────────────────────────────────── */
  .stops-card {
    background: var(--white);
    border-radius: var(--radius);
    margin-bottom: 14px;
    box-shadow: var(--shadow);
    overflow: hidden;
  }
  .stops-card-title {
    background: var(--card-bg);
    border-bottom: 1px solid var(--line);
    padding: 11px 16px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--slate);
  }
  .stop-item {
    display: flex;
    align-items: flex-start;
    gap: 0;
    position: relative;
  }
  .stop-item:not(:last-child)::after {
    content: '';
    position: absolute;
    left: 30px;
    top: 48px;
    bottom: 0;
    width: 2px;
    background: var(--line);
  }
  .stop-left {
    width: 60px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 14px;
  }
  .stop-dot {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--mist);
    border: 2px solid var(--line);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    flex-shrink: 0;
    position: relative;
    z-index: 1;
    background: #fff;
  }
  .stop-dot.start { border-color: var(--green); background: var(--green-pale); }
  .stop-dot.end   { border-color: var(--sky);   background: var(--sky-light); }
  .stop-dot.warn  { border-color: var(--amber);  background: var(--amber-pale); }
  .stop-dot.poi   { border-color: var(--heather); background: #f3eef7; }
  .stop-dot.fuel  { border-color: var(--gold);   background: var(--gold-pale); }

  .stop-right {
    flex: 1;
    padding: 12px 16px 12px 0;
    border-bottom: 1px solid var(--line);
  }
  .stop-item:last-child .stop-right { border-bottom: none; }

  .stop-name {
    font-size: 15px;
    font-weight: 600;
    color: var(--ink);
    margin-bottom: 3px;
    line-height: 1.3;
  }
  .stop-detail {
    font-size: 13px;
    color: var(--slate);
    line-height: 1.4;
    margin-bottom: 6px;
  }
  .stop-link {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: var(--sky-light);
    color: var(--sky);
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 600;
    text-decoration: none;
    transition: background 0.15s;
  }
  .stop-link:active { background: #bfdbfe; }
  .stop-link.green-link { background: var(--green-pale); color: var(--green); }
  .stop-link.warn-link  { background: var(--amber-pale); color: var(--amber); }

  /* ── Notes ────────────────────────────────────────────────── */
  .notes-card {
    background: var(--gold-pale);
    border: 1px solid #f0c040;
    border-radius: var(--radius);
    padding: 14px 16px;
    margin-bottom: 14px;
  }
  .notes-title {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 8px;
  }
  .notes-item {
    font-size: 13px;
    color: #5a3e00;
    padding: 4px 0 4px 16px;
    position: relative;
    line-height: 1.4;
  }
  .notes-item::before {
    content: '•';
    position: absolute;
    left: 4px;
    color: var(--gold);
    font-weight: bold;
  }

  /* ── Overview tab ─────────────────────────────────────────── */
  .overview-grid {
    display: grid;
    gap: 10px;
  }
  .ov-row {
    background: var(--white);
    border-radius: var(--radius);
    padding: 14px 16px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: var(--shadow);
    text-decoration: none;
    color: var(--ink);
    transition: transform 0.15s;
    cursor: pointer;
  }
  .ov-row:active { transform: scale(0.98); }
  .ov-day-badge {
    background: var(--sky);
    color: #fff;
    border-radius: 8px;
    min-width: 44px;
    height: 44px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    flex-shrink: 0;
  }
  .ov-day-badge .dnum { font-size: 18px; line-height: 1; }
  .ov-info { flex: 1; min-width: 0; }
  .ov-date { font-size: 11px; color: var(--slate); margin-bottom: 2px; }
  .ov-title { font-size: 14px; font-weight: 600; line-height: 1.3; }
  .ov-miles { font-size: 12px; color: var(--slate); margin-top: 2px; }
  .ov-arrow { color: var(--line); font-size: 18px; flex-shrink: 0; }

  .ov-row.highlight .ov-day-badge { background: var(--gold); }

  /* ── Emergency contacts ───────────────────────────────────── */
  .contacts-card {
    background: var(--white);
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: var(--shadow);
    margin-bottom: 14px;
  }
  .contact-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--line);
    text-decoration: none;
    color: var(--ink);
  }
  .contact-item:last-child { border-bottom: none; }
  .contact-icon { font-size: 20px; width: 28px; text-align: center; }
  .contact-info { flex: 1; }
  .contact-name { font-size: 14px; font-weight: 600; }
  .contact-num  { font-size: 13px; color: var(--sky); }

  /* ── Section labels ───────────────────────────────────────── */
  .section-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--slate);
    margin: 18px 0 8px;
  }

  /* ── Info panels ──────────────────────────────────────────── */
  .info-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--card-bg);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 13px 16px;
    margin-bottom: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    color: var(--ink);
    -webkit-tap-highlight-color: transparent;
    user-select: none;
  }
  .info-toggle:active { opacity: 0.8; }
  .info-toggle .toggle-icon { font-size: 18px; color: var(--slate); transition: transform 0.2s; }
  .info-toggle.open .toggle-icon { transform: rotate(180deg); }

  .info-panel {
    display: none;
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    overflow: hidden;
    margin-bottom: 14px;
    box-shadow: var(--shadow);
  }
  .info-panel.open { display: block; }

  .info-section {
    border-bottom: 1px solid var(--line);
    padding: 14px 16px;
  }
  .info-section:last-child { border-bottom: none; }
  .info-section-title {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--slate);
    margin-bottom: 10px;
  }
  .info-item {
    padding: 8px 0;
    border-bottom: 1px solid #f0f4fa;
    font-size: 14px;
    line-height: 1.5;
  }
  .info-item:last-child { border-bottom: none; padding-bottom: 0; }
  .info-item strong { color: var(--ink); display: block; margin-bottom: 2px; }
  .info-item .info-detail { color: var(--slate); font-size: 13px; }
  .info-item .info-cost {
    display: inline-block;
    background: var(--green-pale);
    color: var(--green);
    border-radius: 6px;
    padding: 1px 7px;
    font-size: 11px;
    font-weight: 600;
    margin-top: 3px;
  }
  .info-item .info-link {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    color: var(--sky);
    text-decoration: none;
    font-size: 12px;
    font-weight: 600;
    margin-top: 4px;
  }
  .info-alert {
    background: var(--amber-pale);
    border-left: 3px solid var(--amber);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    color: #5a3e00;
    margin: 6px 0;
    line-height: 1.4;
  }
  .info-alert.green {
    background: var(--green-pale);
    border-left-color: var(--green);
    color: #1a4a2e;
  }

  /* ── Ballot reminder ──────────────────────────────────────── */
  .ballot-card {
    background: #fff3cd;
    border: 2px solid var(--gold);
    border-radius: var(--radius);
    padding: 14px 16px;
    margin-bottom: 14px;
  }
  .ballot-title {
    font-size: 13px;
    font-weight: 700;
    color: #7a5000;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }
  .ballot-detail {
    font-size: 13px;
    color: #5a3e00;
    margin-bottom: 8px;
  }
"""

JS = """
function toggleInfo(id) {
  const panel = document.getElementById(id);
  const btn = document.querySelector(`[data-panel="${id}"]`);
  if (panel.classList.contains('open')) {
    panel.classList.remove('open');
    btn.classList.remove('open');
  } else {
    panel.classList.add('open');
    btn.classList.add('open');
  }
}

function showDay(id) {
  document.querySelectorAll('.day-section').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));

  document.getElementById(id).classList.add('active');

  const buttons = document.querySelectorAll('.nav-btn');
  buttons.forEach(btn => {
    if (btn.getAttribute('onclick') === `showDay('${id}')`) {
      btn.classList.add('active');
      btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}
"""

# ── section builders ──────────────────────────────────────────────────────────

def build_head(trip, days):
    dogs = trip['dogs']
    first = datetime.strptime(days[0]['date'], '%Y-%m-%d')
    last  = datetime.strptime(days[-1]['date'], '%Y-%m-%d')
    if first.month == last.month:
        date_range = f"{first.strftime('%-d')}–{last.strftime('%-d %b')}"
    else:
        date_range = f"{first.strftime('%-d %b')} – {last.strftime('%-d %b')}"
    num_days = len(days)
    num_dogs = len(dogs)
    dog_chip = f"🐾 {num_dogs} dog{'s' if num_dogs != 1 else ''}" if num_dogs else ''
    dogs_sub = (' &amp; '.join(h(d['name']) for d in dogs)) if num_dogs else ''
    travellers_line = h(trip['travellers']) + (f' · {dogs_sub}' if dogs_sub else '')
    title = trip.get('title', 'Trip Guide')
    built = datetime.now().strftime('%-d %b %Y %H:%M')
    car_chip = f'🚗 {h(trip["car"]["model"])}' if trip.get('car', {}).get('model') else ''
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>{h(title)} — Route Guide</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+3:wght@300;400;600&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>

<!-- ── Hero ─────────────────────────────────────────────────────────────────── -->
<div class="hero">
  <div class="hero-title">{h(title)}</div>
  <div class="hero-sub">{travellers_line}</div>
  <div class="hero-meta">
    <div class="hero-chip">🗓 {date_range}</div>
    {'<div class="hero-chip">' + car_chip + '</div>' if car_chip else ''}
    <div class="hero-chip">{num_days} days</div>
    {'<div class="hero-chip">' + dog_chip + '</div>' if dog_chip else ''}
    <div class="hero-chip" style="opacity:0.6;font-size:11px">Built {built}</div>
  </div>
</div>
"""


def build_nav(days):
    btns = ['<button class="nav-btn active" onclick="showDay(\'overview\')">Overview</button>']
    for d in days:
        n = d['day']
        flags = d.get('flags', [])
        extras = ''.join(FLAG_EMOJI[f] for f in flags if f in FLAG_EMOJI)
        suffix = f' {extras}' if extras else ''
        btns.append(f'<button class="nav-btn" onclick="showDay(\'d{n}\')">Day {n}{suffix}</button>')
    btns.append('<button class="nav-btn" onclick="showDay(\'contacts\')">📞 SOS</button>')
    return f"""<!-- ── Nav ──────────────────────────────────────────────────────────────────── -->
<div class="nav-wrap">
  <div class="nav-scroll">
    {''.join(btns)}
  </div>
</div>
"""


def ov_miles_line(d):
    miles = d['leg_miles']
    stops = d.get('stops', [])
    key_stops = [s['name'].split(',')[0].split('—')[0].strip() for s in stops[:2]]
    stop_str = ' + '.join(key_stops) if key_stops else ''
    return f'≈ {miles} miles · {stop_str}' if stop_str else f'≈ {miles} miles'


def build_overview(days):
    rows = []
    for d in days:
        n = d['day']
        flags = d.get('flags', [])
        highlight = 'highlight' in flags
        cls = ' highlight' if highlight else ''
        date_str = fmt_date(d['date'])
        flag_emojis = ''.join(FLAG_EMOJI[f] for f in flags if f in FLAG_EMOJI)
        date_display = f'{date_str} {flag_emojis}'.strip()
        miles_line = ov_miles_line(d)
        rows.append(f"""    <div class="ov-row{cls}" onclick="showDay('d{n}')">
      <div class="ov-day-badge"><div class="dnum">{n}</div></div>
      <div class="ov-info">
        <div class="ov-date">{h(date_display)}</div>
        <div class="ov-title">{h(d['title'])}</div>
        <div class="ov-miles">{h(miles_line)}</div>
      </div><div class="ov-arrow">›</div>
    </div>""")

    rows_html = '\n'.join(rows)
    num_days = len(days)
    return f"""<!-- ════════════════════════════════════════════════════════════ OVERVIEW -->
<div id="overview" class="day-section active">
  <p class="section-label">All {num_days} days — tap any to navigate</p>
  <div class="overview-grid">
{rows_html}
  </div>
</div>
"""


def stop_links(stop):
    parts = []
    if stop.get('maps_query'):
        parts.append(f'<a class="stop-link" href="{maps_search(stop["maps_query"])}" target="_blank">📍 Map</a>')
    if stop.get('url'):
        label = '🌐 Book' if stop.get('book_ahead') else '🌐 Website'
        if stop.get('status') == 'not_bookable':
            label = '🌐 Check status'
        parts.append(f'<a class="stop-link green-link" href="{h(stop["url"])}" target="_blank" style="margin-left:6px">{label}</a>')
    return ' '.join(parts)


def dot_class_for(stop_type, position, total):
    if position == 0:
        return 'start'
    if position == total - 1:
        return 'end'
    return STOP_DOT.get(stop_type, 'poi')


def build_stop_item(stop, dot_cls, dot_emoji=None):
    stype = stop.get('type', '')
    if dot_emoji is None:
        dot_emoji = STOP_EMOJI.get(stype, '📍')

    # tidal warning gets special treatment
    name_prefix = '⚠️ ' if stype == 'tidal_warning' else ''
    warn_link = ''
    if stype == 'tidal_warning' and stop.get('tide_check_url'):
        warn_link = f'<a class="stop-link warn-link" href="{h(stop["tide_check_url"])}" target="_blank">🌐 Tide times</a> '

    # Jacobite / train option warning
    if stop.get('status') == 'not_bookable':
        dot_cls = 'warn'

    links = warn_link + stop_links(stop)
    detail = h(stop.get('detail', ''))
    name = h(stop.get('name', ''))

    return f"""    <div class="stop-item">
      <div class="stop-left"><div class="stop-dot {dot_cls}">{dot_emoji}</div></div>
      <div class="stop-right">
        <div class="stop-name">{name_prefix}{name}</div>
        <div class="stop-detail">{detail}</div>
        {links}
      </div>
    </div>"""


def build_stops_card(day, stays_map):
    stops = day.get('stops', [])
    stay_id = day.get('stay_id')
    stay = stays_map.get(stay_id) if stay_id else None

    items = []
    total = len(stops)

    for i, stop in enumerate(stops):
        stype = stop.get('type', '')
        if i == 0:
            dot_cls = 'start'
        elif i == total - 1 and stay:
            dot_cls = 'poi'  # last real stop before accommodation
        else:
            dot_cls = STOP_DOT.get(stype, 'poi')
            if stype == 'tidal_warning':
                dot_cls = 'warn'
        items.append(build_stop_item(stop, dot_cls))

    # Accommodation end stop
    if stay:
        nights = stay.get('nights', 1)
        night_str = f'{nights} nights' if nights > 1 else 'Overnight'
        stay_emoji = STAY_EMOJI.get(stay['type'], '🏡')
        acc_name = h(stay['name'])
        acc_url = stay.get('url', '')
        acc_query = stay.get('location', stay['name'])
        map_link = f'<a class="stop-link" href="{maps_search(acc_query)}" target="_blank">📍 Map</a>'
        web_link = f'<a class="stop-link green-link" href="{h(acc_url)}" target="_blank" style="margin-left:6px">🌐 Website</a>' if acc_url else ''
        is_checkin_day = day.get('date') == stay.get('checkin')
        detail_parts = []
        if stay.get('location'):
            detail_parts.append(h(stay['location']))
        cin = stay.get('checkin_time')
        cout = stay.get('checkout_time')
        if cin or cout:
            times = []
            if cin:
                times.append(f'Check-in {cin}')
            if cout:
                times.append(f'Checkout {cout}')
            detail_parts.append(' · '.join(times))
        if is_checkin_day and stay.get('access'):
            detail_parts.append(f'🔑 {h(stay["access"])}')
        if stay.get('what3words'):
            w3w = h(stay['what3words'])
            detail_parts.append(f'///{w3w}')
        acc_detail = ' — '.join(detail_parts)
        extra_lines = ''
        if is_checkin_day and stay.get('directions'):
            extra_lines += f'\n        <div class="stop-detail">🗺 {h(stay["directions"])}</div>'
        if is_checkin_day and stay.get('hot_water'):
            extra_lines += f'\n        <div class="stop-detail">🚿 {h(stay["hot_water"])}</div>'
        items.append(f"""    <div class="stop-item">
      <div class="stop-left"><div class="stop-dot end">{stay_emoji}</div></div>
      <div class="stop-right">
        <div class="stop-name">{acc_name} — {night_str}</div>
        <div class="stop-detail">{acc_detail}</div>{extra_lines}
        {map_link}{web_link}
      </div>
    </div>""")

    items_html = '\n'.join(items)
    return f"""  <div class="stops-card">
    <div class="stops-card-title">Stops &amp; places of interest</div>
{items_html}
  </div>"""


def build_notes_card(day):
    notes = day.get('notes', [])
    if not notes:
        return ''
    items = '\n'.join(f'    <div class="notes-item">{h(n)}</div>' for n in notes)
    return f"""  <div class="notes-card">
    <div class="notes-title">📌 Notes</div>
{items}
  </div>"""


def build_ballot_card(day):
    br = day.get('ballot_reminder')
    if not br:
        return ''
    return f"""  <div class="ballot-card">
    <div class="ballot-title">⛳ {h(br['action'])}</div>
    <div class="ballot-detail">{h(br.get('detail', ''))}</div>
    <a class="stop-link green-link" href="{h(br.get('url',''))}" target="_blank">🌐 Enter ballot</a>
  </div>"""


def build_info_panel(day, idx, stay=None, dogs=None):
    stops = day.get('stops', [])
    eating = day.get('eating', [])
    notes = day.get('notes', [])
    golf = day.get('golf')
    ebike = day.get('ebike')
    afternoon_tea = day.get('afternoon_tea')
    flags = day.get('flags', [])

    sections = []

    # ── Golf section ─────────────────────────────────────────
    if golf:
        cost_str = f'~£{golf["cost_gbp"]} with hire' if golf.get('hire_included') else f'~£{golf["cost_gbp"]}'
        if golf.get('cost_gbp') == 0:
            cost_str = 'Free (hire included)'
        booking_note = h(golf.get('booking', ''))
        dog_note = '🐾 Dogs welcome on site' if golf.get('dogs_welcome') else '🐕 Leave dogs at accommodation'
        url_link = f'<a class="info-link" href="{h(golf["url"])}" target="_blank">🌐 Open</a>' if golf.get('url') else ''
        sections.append(f"""<div class="info-section"><div class="info-section-title">⛳ {h(golf['course'])}</div>
<div class="info-item"><strong>{golf['holes']}-hole course</strong><span class="info-detail">{booking_note}. {dog_note}.</span><br><span class="info-cost">{cost_str}</span> {url_link}</div></div>""")

    # ── Afternoon tea section ─────────────────────────────────
    if afternoon_tea:
        at_url = f'<a class="info-link" href="{h(afternoon_tea["url"])}" target="_blank">🌐 Open</a>' if afternoon_tea.get('url') else ''
        sections.append(f"""<div class="info-section"><div class="info-section-title">☕ Afternoon tea option</div>
<div class="info-item"><strong>{h(afternoon_tea['name'])}</strong><span class="info-detail">{h(afternoon_tea.get('detail',''))}</span><br><span class="info-cost">{h(afternoon_tea.get('cost',''))}</span> {at_url}</div></div>""")

    # ── Activities section ────────────────────────────────────
    dogs = dogs or []
    dog_stops = [s for s in stops if s.get('type', '') not in ('fuel', 'lunch_fuel')]
    if dog_stops:
        items = []
        for s in dog_stops:
            stype = s.get('type', '')
            emoji = STOP_EMOJI.get(stype, '📍')
            name = h(s['name'])
            detail = h(s.get('detail', ''))
            cost = s.get('cost')
            url = s.get('url')
            maps_q = s.get('maps_query')
            link_href = url if url else (maps_search(maps_q) if maps_q else '')
            link_html = f'<a class="info-link" href="{h(link_href)}" target="_blank">🌐 Open</a>' if link_href else ''
            cost_html = f'<br><span class="info-cost">{h(cost)}</span>' if cost else ''
            items.append(f'<div class="info-item"><strong>{name}</strong><span class="info-detail">{detail}</span>{cost_html} {link_html}</div>')
        if 'train' in flags:
            title = '🚂 Train &amp; activities'
        elif 'golf' in flags:
            if dogs:
                title = '🐾 &amp; ⛳ Activities'
            else:
                title = '⛳ Activities'
        elif dogs:
            dog_names = ' &amp; '.join(h(d['name']) for d in dogs)
            title = f'🐾 With {dog_names}'
        else:
            title = '📍 Activities'
        sections.append(f'<div class="info-section"><div class="info-section-title">{title}</div>{"".join(items)}</div>')

    # ── Eating section ────────────────────────────────────────
    if eating:
        items = []
        for e in eating:
            name = h(e['name'])
            detail = h(e.get('detail', ''))
            url = e.get('url')
            maps_q = e.get('maps_query')
            link_href = url if url else (maps_search(maps_q) if maps_q else '')
            link_html = f'<a class="info-link" href="{h(link_href)}" target="_blank">🌐 Open</a>' if link_href else ''
            dog_icon = '🐾' if e.get('dog_friendly') else '🚫'
            items.append(f'<div class="info-item"><strong>{name}</strong><span class="info-detail">{detail}</span> {link_html}</div>')
        sections.append(f'<div class="info-section"><div class="info-section-title">🍽 Eating</div>{"".join(items)}</div>')

    # ── Tips section ──────────────────────────────────────────
    if notes:
        alerts = []
        for n in notes:
            nl = n.lower()
            is_green = any(x in nl for x in ['plug in', 'charge', '🔌', 'free', 'good', 'enjoy', 'lothian', 'bus', 'stock', 'book', 'call'])
            cls = 'info-alert green' if is_green else 'info-alert'
            alerts.append(f'<div class="{cls}">{h(n)}</div>')
        sections.append(f'<div class="info-section"><div class="info-section-title">📌 Tips</div>{"".join(alerts)}</div>')

    # ── Road bike section ─────────────────────────────────────
    if stay:
        bike_hire = stay.get('bike_hire')
        climbs_url = stay.get('climbs_url', '')
        if bike_hire or climbs_url:
            items = []
            if bike_hire:
                bh_url = h(bike_hire.get('url', ''))
                bh_link = f'<a class="info-link" href="{bh_url}" target="_blank">🌐 Find</a>' if bh_url else ''
                climb_note = h(bike_hire.get('climb_note', bike_hire.get('note', '')))
                items.append(f'<div class="info-item"><strong>{h(bike_hire["name"])}</strong><span class="info-detail">{climb_note}</span> {bh_link}</div>')
            if climbs_url:
                items.append(f'<div class="info-item"><strong>Cycling climbs near here — ClimbFinder</strong><span class="info-detail">Named climbs with elevation profiles, gradients, and Strava segments for this region.</span> <a class="info-link" href="{h(climbs_url)}" target="_blank">🏔 Open</a></div>')
            sections.append(f'<div class="info-section"><div class="info-section-title">🚴 Road cycling</div>{"".join(items)}</div>')

    if not sections:
        return ''

    panel_id = f'p{idx}'
    return f"""  <div class="info-toggle" data-panel="{panel_id}" onclick="toggleInfo('{panel_id}')">
    <span>🗒 Activities, eating &amp; tips</span>
    <span class="toggle-icon">⌄</span>
  </div>
  <div id="{panel_id}" class="info-panel">
{''.join(sections)}  </div>
"""


def map_subtitle(waypoints):
    if len(waypoints) <= 2:
        return f'{waypoints[0].split(" ")[0]} → {waypoints[-1].split(" ")[0]}'
    key = [waypoints[0], waypoints[len(waypoints)//2], waypoints[-1]]
    return ' → '.join(w.split(',')[0].split(' ')[0:3] for w in key)


def day_stats(d, dogs=None):
    flags = d.get('flags', [])
    miles = d['leg_miles']
    hours = d['leg_drive_hours']
    walk = d.get('total_walk_miles', 0)
    stops = d.get('stops', [])
    walk_icon = '🐾' if dogs else '🚶'

    stats = [f'🚗 <span>≈ {miles} miles</span>']

    if hours >= 1:
        h_str = f'{int(hours)} hr' if hours == int(hours) else f'{hours} hrs'
        stats.append(f'⏱ <span>≈ {h_str}</span>')

    if walk > 0:
        steps = round(walk * 2000 / 100) * 100
        step_cls = 'green' if steps < 10000 else ('amber' if steps <= 15000 else 'red')
        steps_fmt = f'{steps:,}'
        stats.append(f'{walk_icon} <span>{walk} miles</span> <span class="step-badge {step_cls}">~{steps_fmt} steps</span>')

    if 'golf' in flags and d.get('golf'):
        g = d['golf']
        stats.append(f'⛳ <span>{g["holes"]}-hole golf</span>')
    elif 'train' in flags:
        stats.append('🚂 <span>Train day</span>')
    elif 'ebike' in flags:
        stats.append('🚲 <span>E-bike option</span>')

    return '\n      '.join(f'<div class="day-stat">{s}</div>' for s in stats)


def build_day_section(day, stays_map, dogs=None):
    n = day['day']
    flags = day.get('flags', [])
    flag_emojis = ''.join(FLAG_EMOJI[f] for f in flags if f in FLAG_EMOJI)
    date_str = fmt_date(day['date'])
    date_display = f'{date_str} {flag_emojis}'.strip()

    waypoints = day.get('map_waypoints', [])
    map_url = maps_dir(waypoints) if waypoints else '#'
    weather_url = day.get('weather_url', '')

    # Subtitle from first and last waypoint
    if len(waypoints) >= 2:
        start_w = waypoints[0].split(',')[0]
        end_w = waypoints[-1].split(',')[0]
        mid_waypoints = waypoints[1:-1][:2]
        mid_str = ' → '.join(w.split(',')[0] for w in mid_waypoints)
        subtitle = f'{start_w} → {mid_str} → {end_w}' if mid_str else f'{start_w} → {end_w}'
    else:
        subtitle = day['title']

    stops_card = build_stops_card(day, stays_map)
    notes_card = build_notes_card(day)
    ballot_card = build_ballot_card(day)
    stay = stays_map.get(day.get('stay_id')) if day.get('stay_id') else None
    info_panel = build_info_panel(day, n, stay, dogs=dogs)

    return f"""
<!-- ════════════════════════════════════════════════════════════ DAY {n} -->
<div id="d{n}" class="day-section">
  <div class="day-header">
    <div class="day-number">Day {n} · {h(date_display)}</div>
    <div class="day-title">{h(day['title'])}</div>
    <div class="day-stats">
      {day_stats(day, dogs=dogs)}
    </div>
  </div>
  <a class="map-btn" href="{map_url}" target="_blank">
    <span class="map-icon">🗺</span>
    <div class="map-btn-text">Open full route in Maps<small>{h(subtitle)}</small></div>
  </a>
  {'<a class="weather-btn" href="' + h(weather_url) + '" target="_blank">🌤 Check BBC Weather for today</a>' if weather_url else ''}
{stops_card}
{notes_card}
{ballot_card}
{info_panel}
</div>
"""


def build_contacts(emergency, bookings):
    vets_html = ''
    for v in emergency.get('vets', []):
        phone_clean = v['phone'].replace(' ', '')
        vets_html += f"""    <a class="contact-item" href="tel:{phone_clean}">
      <div class="contact-icon">🐾</div>
      <div class="contact-info">
        <div class="contact-name">{h(v['name'])}</div>
        <div class="contact-num">{h(v['phone'])}</div>
      </div>
    </a>
"""

    hospitals_html = ''
    for hosp in emergency.get('hospitals', []):
        query = hosp.get('maps_query', hosp['name'])
        hospitals_html += f"""    <a class="contact-item" href="{maps_search(query)}" target="_blank">
      <div class="contact-icon">🏥</div>
      <div class="contact-info">
        <div class="contact-name">{h(hosp['name'])}</div>
        <div class="contact-num">Tap for map →</div>
      </div>
    </a>
"""

    bookings_html = ''
    priority_bookings = [b for b in bookings if b.get('priority', 99) <= 2]
    for b in priority_bookings[:6]:
        icon = '🚂' if 'Jacobite' in b['item'] else '⛳' if 'Ballot' in b['item'] or 'Golf' in b['item'] else '🌊' if 'Tide' in b['item'] or 'Holy' in b['item'] else '🚠' if 'Gondola' in b['item'] or 'Nevis' in b['item'] else '🔖'
        url = b.get('url', '#')
        display_url = url.replace('https://', '').replace('http://', '').split('/')[0]
        bookings_html += f"""    <a class="contact-item" href="{h(url)}" target="_blank">
      <div class="contact-icon">{icon}</div>
      <div class="contact-info">
        <div class="contact-name">{h(b['item'])}</div>
        <div class="contact-num">{h(display_url)}</div>
      </div>
    </a>
"""

    emergency_num = emergency.get('emergency', '999')
    nhs_num = emergency.get('nhs_non_emergency', '111')

    return f"""
<!-- ════════════════════════════════════════════════════════════ CONTACTS -->
<div id="contacts" class="day-section">
  <div class="day-header">
    <div class="day-number">Emergency contacts</div>
    <div class="day-title">SOS — Vets, Hospitals &amp; Services</div>
    <div class="day-stats">
      <div class="day-stat">🚨 <span>Save these numbers</span></div>
    </div>
  </div>
  <p class="section-label">Emergency services</p>
  <div class="contacts-card">
    <a class="contact-item" href="tel:{emergency_num}">
      <div class="contact-icon">🚨</div>
      <div class="contact-info">
        <div class="contact-name">Emergency (Police / Ambulance / Mountain Rescue)</div>
        <div class="contact-num">{emergency_num}</div>
      </div>
    </a>
    <a class="contact-item" href="tel:{nhs_num}">
      <div class="contact-icon">🏥</div>
      <div class="contact-info">
        <div class="contact-name">NHS {nhs_num} — Non-emergency medical advice</div>
        <div class="contact-num">{nhs_num}</div>
      </div>
    </a>
  </div>
  <p class="section-label">Vets near the route</p>
  <div class="contacts-card">
{vets_html}  </div>
  <p class="section-label">Hospitals near the route</p>
  <div class="contacts-card">
{hospitals_html}  </div>
  <p class="section-label">Key bookings to check</p>
  <div class="contacts-card">
{bookings_html}  </div>
</div>
"""


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trip', default='scotland-2026', help='Trip ID (folder name under trips/)')
    args = parser.parse_args()

    trip_dir = os.path.join(BASE, 'trips', args.trip)
    data_path = os.path.join(trip_dir, 'data.json')
    out_path  = os.path.join(trip_dir, 'output', 'index.html')

    with open(data_path) as f:
        data = json.load(f)

    trip = data['trip']
    stays_map = {s['id']: s for s in data['stays']}
    days = data['days']
    emergency = data.get('emergency_contacts', {})
    bookings = data.get('bookings_required', [])

    parts = [build_head(trip, days), build_nav(days)]
    parts.append('\n<!-- ── Content ───────────────────────────────────────────────────────────────── -->')
    parts.append('<div class="content">\n')
    parts.append(build_overview(days))

    for day in days:
        parts.append(build_day_section(day, stays_map, dogs=trip.get('dogs', [])))

    parts.append(build_contacts(emergency, bookings))
    parts.append('\n</div><!-- end .content -->\n')
    parts.append(f'\n<script>\n{JS}\n</script>\n\n</body></html>')

    html_out = ''.join(parts)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_out)

    print(f"✓ Written {len(html_out):,} bytes → {out_path}")
    print(f"  {len(days)} days, {len(stays_map)} stays")


if __name__ == '__main__':
    main()

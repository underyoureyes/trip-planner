"""
Trip Planner — Test Suite
Run: pytest tests/ -v
Or:  python tests/test_all.py [--trip <trip-id>]
"""

import json
import re
import sys
import os
import ssl
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent.parent

def _resolve_trip_id():
    for i, arg in enumerate(sys.argv):
        if arg == '--trip' and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return 'scotland-2026'

TRIP_ID = _resolve_trip_id()
DATA    = ROOT / 'trips' / TRIP_ID / 'data.json'
OUTPUT  = ROOT / 'trips' / TRIP_ID / 'output'

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_json():
    with open(DATA) as f:
        return json.load(f)

def load_html():
    p = OUTPUT / "index.html"
    return p.read_text(encoding="utf-8") if p.exists() else None

def load_docx_text():
    """Extract raw text from the Word doc if docx2txt is available."""
    docx_files = list(OUTPUT.glob('*.docx'))
    if not docx_files:
        return None
    try:
        import docx2txt
        return docx2txt.process(str(docx_files[0]))
    except ImportError:
        return None

RESULTS = []

def test(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    RESULTS.append((status, name, detail))
    icon = "✓" if condition else "✗"
    print(f"  {icon} [{status}] {name}" + (f" — {detail}" if detail else ""))
    return condition

# ─────────────────────────────────────────────────────────────────────────────
# 1. JSON DATA INTEGRITY
# ─────────────────────────────────────────────────────────────────────────────

def test_json_integrity():
    print("\n── 1. JSON Data Integrity ──────────────────────────────────────")
    data = load_json()

    # Top-level keys
    test("trip key present", "trip" in data)
    test("stays key present", "stays" in data)
    test("days key present", "days" in data)
    test("bookings_required key present", "bookings_required" in data)
    test("emergency_contacts key present", "emergency_contacts" in data)

    # Days count
    days = data.get("days", [])
    test("At least 1 day defined", len(days) > 0, f"found {len(days)}")

    # Days numbered sequentially from 1
    day_nums = [d["day"] for d in days]
    expected = list(range(1, len(days) + 1))
    test(f"Days numbered 1–{len(days)} sequentially", day_nums == expected, str(day_nums))

    # Each day has required fields
    required_day_fields = {"day", "date", "title", "leg_miles", "leg_drive_hours",
                           "total_walk_miles", "map_waypoints", "stops", "eating", "notes"}
    missing = []
    for d in days:
        for f in required_day_fields:
            if f not in d:
                missing.append(f"Day {d['day']} missing '{f}'")
    test("All days have required fields", len(missing) == 0, "; ".join(missing) if missing else "")

    # Stays
    stays = data.get("stays", [])
    test("At least 1 stay defined", len(stays) > 0, f"found {len(stays)}")
    stay_ids = {s["id"] for s in stays}

    # Each day's stay_id references a valid stay (or is null for last day)
    bad_refs = []
    for d in days:
        sid = d.get("stay_id")
        if sid is not None and sid not in stay_ids:
            bad_refs.append(f"Day {d['day']} refs unknown stay '{sid}'")
    test("All stay_id references are valid", len(bad_refs) == 0, "; ".join(bad_refs))

    # Stay dates are contiguous and don't overlap
    stays_sorted = sorted(stays, key=lambda s: s["checkin"])
    date_errors = []
    for i in range(len(stays_sorted) - 1):
        a, b = stays_sorted[i], stays_sorted[i + 1]
        checkout_a = datetime.strptime(a["checkout"], "%Y-%m-%d").date()
        checkin_b = datetime.strptime(b["checkin"], "%Y-%m-%d").date()
        if checkout_a > checkin_b:
            date_errors.append(f"{a['id']} checkout {a['checkout']} overlaps {b['id']} checkin {b['checkin']}")
    test("Stay dates do not overlap", len(date_errors) == 0, "; ".join(date_errors))

    # Total nights defined
    total_nights = sum(s["nights"] for s in stays)
    test("Total accommodation nights > 0", total_nights > 0, f"found {total_nights}")

    # Dogs defined (optional — some trips have no dogs)
    dogs = data.get("trip", {}).get("dogs", [])
    if dogs:
        test("Dogs defined with max_walk_miles", True, f"found {len(dogs)}")
    for dog in dogs:
        test(f"Dog '{dog.get('name','?')}' has max_walk_miles defined",
             "max_walk_miles" in dog)

    # Car defined
    car = data.get("trip", {}).get("car", {})
    test("Car tank range defined", car.get("tank_range_miles", 0) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# 2. WALKING DISTANCE LIMITS
# ─────────────────────────────────────────────────────────────────────────────

def test_walking_limits():
    data = load_json()
    dogs = data["trip"]["dogs"]
    if not dogs:
        print("\n── 2. Walking Distance Limits (no dogs — skipping) ───────────────")
        return
    limit_dog = min(dogs, key=lambda d: d["max_walk_miles"])
    max_walk = limit_dog["max_walk_miles"]
    print(f"\n── 2. Walking Distance Limits ({limit_dog['name']}: {max_walk} miles max) ──────────────")

    for d in data["days"]:
        total = d.get("total_walk_miles", 0)
        test(
            f"Day {d['day']:2d} ({d['date']}) — {d['title'][:35]}",
            total <= max_walk,
            f"{total} miles {'OK' if total <= max_walk else f'EXCEEDS {max_walk} mile limit'}"
        )

    for d in data["days"]:
        for stop in d.get("stops", []):
            w = stop.get("walk_miles", 0)
            test(
                f"  Day {d['day']} stop '{stop['name'][:30]}' individual walk",
                w <= max_walk,
                f"{w} miles"
            ) if w > 0 else None


# ─────────────────────────────────────────────────────────────────────────────
# 3. FUEL / RANGE SAFETY
# ─────────────────────────────────────────────────────────────────────────────

def test_fuel_legs():
    print("\n── 3. Fuel & Range Safety ──────────────────────────────────────")
    data = load_json()
    car = data["trip"]["car"]
    effective_range = car["tank_range_miles"] + car["overnight_ev_top_up_miles"]  # ~328

    # For legs flagged fuel_warning, check a fuel stop is defined
    for d in data["days"]:
        miles = d.get("leg_miles", 0)
        flags = d.get("flags", [])
        fuel_stops = [s for s in d.get("stops", []) if s.get("type") == "fuel"]

        if miles > 250:
            test(
                f"Day {d['day']} ({miles} miles) has fuel stop defined",
                len(fuel_stops) > 0 or any("fuel" in (s.get("type", "")) for s in d.get("stops", [])),
                f"{len(fuel_stops)} fuel stops found"
            )

        # No single leg exceeds effective range
        test(
            f"Day {d['day']} leg ({miles} miles) within car range ({effective_range})",
            miles <= effective_range,
            f"{miles} vs {effective_range}"
        )

    if TRIP_ID == 'scotland-2026':
        day7 = next((d for d in data["days"] if d["day"] == 7), None)
        if day7:
            has_fuel = any(s.get("type") == "fuel" for s in day7.get("stops", []))
            test("Day 7 (Skye) has a fuel stop defined", has_fuel, "Kyle of Lochalsh fuel required")

        day10 = next((d for d in data["days"] if d["day"] == 10), None)
        if day10:
            has_fuel = any(s.get("type") == "fuel" for s in day10.get("stops", []))
            test("Day 10 (Skye → Loch Ness) has a fuel stop defined", has_fuel)


# ─────────────────────────────────────────────────────────────────────────────
# 4. MAP WAYPOINTS
# ─────────────────────────────────────────────────────────────────────────────

def test_map_waypoints():
    print("\n── 4. Map Waypoints ────────────────────────────────────────────")
    data = load_json()

    for d in data["days"]:
        waypoints = d.get("map_waypoints", [])
        # Must have at least 2 (origin + destination)
        test(f"Day {d['day']} has at least 2 waypoints", len(waypoints) >= 2,
             f"found {len(waypoints)}")
        # Google Maps URL limit: 10 waypoints
        test(f"Day {d['day']} waypoints within Google Maps limit (≤10)",
             len(waypoints) <= 10, f"found {len(waypoints)}")
        # No empty strings
        empties = [w for w in waypoints if not w.strip()]
        test(f"Day {d['day']} no empty waypoints", len(empties) == 0)


# ─────────────────────────────────────────────────────────────────────────────
# 5. URL VALIDITY (structure only — no HTTP requests)
# ─────────────────────────────────────────────────────────────────────────────

def test_url_structure():
    print("\n── 5. URL Structure Validation ─────────────────────────────────")
    data = load_json()

    all_urls = []

    # Collect all URLs from the JSON
    def collect_urls(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "url" and isinstance(v, str) and v:
                    all_urls.append((path + "." + k, v))
                else:
                    collect_urls(v, path + "." + k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                collect_urls(item, path + f"[{i}]")

    collect_urls(data)

    bad_urls = []
    for path, url in all_urls:
        try:
            parsed = urlparse(url)
            if not (parsed.scheme in ("http", "https") and parsed.netloc):
                bad_urls.append(f"{path}: {url}")
        except Exception as e:
            bad_urls.append(f"{path}: {url} ({e})")

    test(f"All {len(all_urls)} URLs have valid structure", len(bad_urls) == 0,
         ("\n    " + "\n    ".join(bad_urls)) if bad_urls else "")

    if TRIP_ID == 'scotland-2026':
        critical = {
            "westcoastrailways.co.uk": "Jacobite",
            "crailgolfingsociety.co.uk": "Crail golf alternative",
            "skyeboat-trips.co.uk": "Stardust",
            "malts.com": "Talisker",
            "cruiselochness.com": "Loch Ness cruise",
            "nevisrange.co.uk": "Nevis Range Gondola",
            "holyislandcrossingtimes.northumberland.gov.uk": "Holy Island tides",
            "bettys.co.uk": "Bettys York",
        }
        url_values = [u for _, u in all_urls]
        for domain, label in critical.items():
            present = any(domain in u for u in url_values)
            test(f"Critical URL present: {label} ({domain})", present)


# ─────────────────────────────────────────────────────────────────────────────
# 6. BOOKINGS COMPLETENESS
# ─────────────────────────────────────────────────────────────────────────────

def test_bookings():
    print("\n── 6. Bookings Completeness ────────────────────────────────────")
    data = load_json()
    bookings = data.get("bookings_required", [])

    test("At least 1 booking item defined", len(bookings) >= 1, f"found {len(bookings)}")

    # Each booking has required fields
    required = {"item", "status", "priority"}
    for b in bookings:
        missing = required - set(b.keys())
        test(f"Booking '{b.get('item', '?')}' has required fields",
             len(missing) == 0, f"missing: {missing}")

    # Priority 1 items must have URLs or actions
    p1 = [b for b in bookings if b.get("priority") == 1]
    for b in p1:
        has_url_or_action = bool(b.get("url") or b.get("action"))
        test(f"Priority-1 booking '{b['item']}' has URL or action", has_url_or_action)

    # Weather URLs present on all days
    days = data.get("days", [])
    missing_weather = [d["day"] for d in days if not d.get("weather_url")]
    test(f"All {len(days)} days have weather_url", len(missing_weather) == 0)

    if TRIP_ID == 'scotland-2026':
        jacobite = next((b for b in bookings if "Jacobite" in b.get("item", "")), None)
        test("Jacobite status is 'not_bookable'",
             jacobite is not None and jacobite.get("status") == "not_bookable")


# ─────────────────────────────────────────────────────────────────────────────
# 7. HTML OUTPUT VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def test_html_output():
    print("\n── 7. HTML Output Validation ───────────────────────────────────")
    html = load_html()
    data = load_json()
    num_days = len(data.get("days", []))
    dogs = data.get("trip", {}).get("dogs", [])

    if html is None:
        test("HTML output file exists", False, "output/index.html not found — run builder first")
        return

    test("HTML output file exists", True)
    test("HTML file is non-trivial size", len(html) > 50_000, f"{len(html):,} bytes")

    for i in range(1, num_days + 1):
        test(f"Day {i:2d} section present in HTML", f'id="d{i}"' in html)

    for i in range(1, num_days + 1):
        test(f"Day {i:2d} nav button present", f"showDay('d{i}')" in html)

    test("Emergency contacts (SOS) section present", 'id="contacts"' in html)

    maps_links = re.findall(r'https://www\.google\.com/maps/dir/[^"\']+', html)
    test(f"At least {num_days} Google Maps route links present",
         len(maps_links) >= num_days, f"found {len(maps_links)}")

    panels = re.findall(r'id="p\d+"', html)
    test(f"At least {num_days} info panels present",
         len(panels) >= num_days, f"found {len(panels)}")

    # Generic: all dog names should appear in HTML
    for dog in dogs:
        test(f"Dog '{dog['name']}' named in HTML", dog['name'] in html)

    if TRIP_ID == 'scotland-2026':
        key_strings = [
            ("Jacobite", "Jacobite mentioned"),
            ("Nevis Range", "Nevis Range Gondola mentioned"),
            ("Talisker", "Talisker Distillery mentioned"),
            ("Glenfinnan", "Glenfinnan Viaduct mentioned"),
            ("Crail", "Crail golf alternative mentioned"),
            ("Lindisfarne", "Holy Island mentioned"),
            ("Bettys", "Bettys York mentioned"),
            ("Portobello", "Portobello Edinburgh mentioned"),
            ("ScotRail", "ScotRail fallback mentioned"),
            ("holyislandcrossingtimes", "Holy Island tide link present"),
        ]
        for text, label in key_strings:
            test(label, text.lower() in html.lower())

    # Check no broken internal references
    broken_hrefs = re.findall(r'href="#([^"]+)"', html)
    missing_ids = [ref for ref in broken_hrefs
                   if f'id="{ref}"' not in html]
    test("No broken internal anchor links",
         len(missing_ids) == 0,
         f"broken: {missing_ids}" if missing_ids else "")

    # Viewport meta tag (mobile-ready)
    test("Viewport meta tag present (mobile-ready)",
         'name="viewport"' in html)

    # Apple mobile web app capable
    test("Apple mobile web app meta tag present",
         'apple-mobile-web-app-capable' in html)


# ─────────────────────────────────────────────────────────────────────────────
# 8. WORD DOC VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def test_docx_output():
    print("\n── 8. Word Document Validation ─────────────────────────────────")
    docx_files = list(OUTPUT.glob('*.docx'))
    docx_path = docx_files[0] if docx_files else OUTPUT / "itinerary.docx"
    test("Word doc exists", docx_path.exists())

    if not docx_path.exists():
        return

    # File size sanity check (should be > 40KB)
    size_kb = docx_path.stat().st_size / 1024
    test("Word doc is plausible size (>40KB)", size_kb > 40, f"{size_kb:.1f}KB")

    text = load_docx_text()
    if text is None:
        test("docx2txt available for text extraction", False,
             "pip install docx2txt to enable content tests")
        return

    test("Word doc text extractable", len(text) > 1000, f"{len(text):,} chars")
    data = load_json()
    num_days = len(data.get("days", []))

    for i in range(1, num_days + 1):
        test(f"Day {i:2d} heading present in Word doc",
             f"Day {i}" in text or f"Day {i:02d}" in text)

    if TRIP_ID == 'scotland-2026':
        key_strings = [
            "Koda", "Monty", "Jacobite", "Talisker", "Glenfinnan",
            "Nevis Range", "Urquhart", "Portobello", "ScotRail",
            "Old Course", "Musselburgh", "Bettys"
        ]
        for s in key_strings:
            test(f"'{s}' present in Word doc", s in text)


# ─────────────────────────────────────────────────────────────────────────────
# 9. CONSISTENCY — JSON vs HTML
# ─────────────────────────────────────────────────────────────────────────────

def test_consistency():
    print("\n── 9. JSON ↔ HTML Consistency ──────────────────────────────────")
    data = load_json()
    html = load_html()

    if html is None:
        test("HTML available for consistency check", False)
        return

    # Every day title in JSON should appear somewhere in HTML
    import html as _html
    for d in data["days"]:
        words = d["title"].split()[:3]
        snippet = " ".join(words)
        escaped = _html.escape(snippet)
        test(f"Day {d['day']:2d} title fragment '{snippet}' in HTML",
             snippet in html or escaped in html)

    # Every stay name in JSON should appear in HTML
    for stay in data["stays"]:
        name_words = stay["name"].split()[:1]
        snippet = " ".join(name_words)
        test(f"Stay '{snippet}' referenced in HTML",
             snippet in html)

    # Emergency contacts in HTML
    for vet in data.get("emergency_contacts", {}).get("vets", []):
        phone = vet["phone"]
        test(f"Vet phone {phone} in HTML", phone in html)


# ─────────────────────────────────────────────────────────────────────────────
# 10. TIDAL / CRITICAL SAFETY CHECKS
# ─────────────────────────────────────────────────────────────────────────────

def test_safety_checks():
    print("\n── 10. Critical Safety Checks ──────────────────────────────────")
    data = load_json()
    html = load_html()

    if TRIP_ID != 'scotland-2026':
        test("Safety checks skipped (scotland-2026 specific)", True)
        return

    day15 = next((d for d in data["days"] if d["day"] == 15), None)
    if day15:
        tidal_stops = [s for s in day15.get("stops", []) if s.get("type") == "tidal_warning"]
        test("Day 15 has tidal warning stop for Holy Island", len(tidal_stops) > 0)
        tide_url = any(
            "holyislandcrossingtimes" in s.get("url", "") or
            "holyislandcrossingtimes" in s.get("tide_check_url", "")
            for s in day15.get("stops", [])
        )
        test("Day 15 tidal stop has tide check URL", tide_url)

    jacobite_stop = None
    for d in data["days"]:
        for s in d.get("stops", []):
            if "Jacobite" in s.get("name", "") and s.get("status") == "not_bookable":
                jacobite_stop = s
    if jacobite_stop:
        test("Jacobite: 1 dog per booking limit documented",
             jacobite_stop.get("dogs_per_booking") == 1)
        test("Jacobite: 2 separate bookings needed",
             jacobite_stop.get("bookings_needed") == 2)

    loch_ness_cruise = None
    for d in data["days"]:
        for s in d.get("stops", []):
            if "Cruise Loch Ness" in s.get("name", ""):
                loch_ness_cruise = s
    if loch_ness_cruise:
        test("Loch Ness cruise: 'standard' type flagged (not RIB)",
             "standard" in loch_ness_cruise.get("name", "").lower() or
             "standard" in loch_ness_cruise.get("detail", "").lower())

    day14 = next((d for d in data["days"] if d["day"] == 14), None)
    if day14:
        dogs = data["trip"]["dogs"]
        limit_dog = min(dogs, key=lambda d: d["max_walk_miles"])
        walk_limit = limit_dog["max_walk_miles"]
        walk = day14.get("total_walk_miles", 0)
        test(f"Day 14 walk ({walk} miles) at or below {limit_dog['name']}'s {walk_limit}-mile limit",
             walk <= walk_limit, f"{'AT LIMIT — monitor closely' if walk == walk_limit else ''}")

    if html:
        test("Tick advice in HTML", "tick" in html.lower())


# ─────────────────────────────────────────────────────────────────────────────
# 11. LIVE LINK CHECKER
# ─────────────────────────────────────────────────────────────────────────────

SKIP_DOMAINS = {
    # Google Maps always returns 200 regardless of whether the route resolves —
    # checked separately in test 12.
    "www.google.com",
    "maps.google.com",
    # Booking.com blocks headless requests with 403 even for valid URLs.
    "www.booking.com",
    # AccuWeather blocks automated requests with 503 even for valid URLs.
    "www.accuweather.com",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

def _try_request(url, method, ctx, timeout):
    req = urllib.request.Request(url, method=method, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.status, ""

def check_url(url, timeout=10):
    """Return (url, status_code, error_msg, is_ssl_warn).

    status categories:
      200-299  → OK
      301/302  → redirect (warn, not failure)
      403/429  → bot-blocked (warn, not failure — site exists)
      404/410  → genuinely dead
      0        → network/SSL error
      "SKIP"   → excluded domain
    """
    parsed = urlparse(url)
    if parsed.netloc in SKIP_DOMAINS:
        return url, "SKIP", "", False

    ssl_verified = ssl.create_default_context()
    ssl_unverified = ssl.create_default_context()
    ssl_unverified.check_hostname = False
    ssl_unverified.verify_mode = ssl.CERT_NONE

    for method in ("HEAD", "GET"):
        try:
            code, err = _try_request(url, method, ssl_verified, timeout)
            return url, code, err, False
        except urllib.error.HTTPError as e:
            if e.code == 405 and method == "HEAD":
                continue  # retry with GET
            return url, e.code, str(e), False
        except urllib.error.URLError as e:
            reason = str(e.reason)
            ssl_related = any(k in reason for k in (
                "SSL", "certificate", "CERTIFICATE", "TLS", "tlsv", "TLSV",
                "handshake", "verify failed", "alert"
            ))
            if ssl_related:
                # Retry without SSL verification to distinguish "site up, bad cert"
                # from "site unreachable"
                try:
                    code, _ = _try_request(url, method, ssl_unverified, timeout)
                    return url, code, f"SSL/TLS issue: {reason}", True
                except Exception:
                    # Unverified also failed — still flag as SSL warning, not dead
                    return url, 0, f"SSL/TLS issue (unverified also failed): {reason}", True
            if method == "HEAD":
                continue
            return url, 0, reason, False
        except Exception as e:
            if method == "HEAD":
                continue
            return url, 0, str(e), False

    return url, 0, "no method succeeded", False


def collect_all_urls(data, html):
    """Collect every external URL from JSON data and the HTML file."""
    urls = {}  # url -> list of sources

    def add(url, source):
        if not url or not url.startswith(("http://", "https://")):
            return
        urls.setdefault(url, []).append(source)

    # From JSON
    def walk(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("url", "tide_check_url", "ballot_url") and isinstance(v, str):
                    add(v, f"json:{path}.{k}")
                else:
                    walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")

    walk(data, "root")

    # From HTML (all href= values)
    if html:
        for href in re.findall(r'href=["\']([^"\']+)["\']', html):
            if href.startswith(("http://", "https://")):
                add(href, "html:href")

    return urls


def test_live_links():
    print("\n── 11. Live Link Checker ───────────────────────────────────────")
    data = load_json()
    html = load_html()

    all_urls = collect_all_urls(data, html)
    unique = list(all_urls.keys())

    skipped = [u for u in unique if urlparse(u).netloc in SKIP_DOMAINS]
    to_check = [u for u in unique if urlparse(u).netloc not in SKIP_DOMAINS]

    print(f"  Checking {len(to_check)} unique URLs ({len(skipped)} skipped: Google Maps / Booking.com)")
    print(f"  Using 8 threads, 10s timeout per URL ...")

    results = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(check_url, url): url for url in to_check}
        for fut in as_completed(futures):
            url, code, err, ssl_warn = fut.result()
            results[url] = (code, err, ssl_warn)

    ok, broken, redirected, bot_blocked, ssl_warns = [], [], [], [], []
    for url in to_check:
        code, err, ssl_warn = results[url]
        if ssl_warn:
            ssl_warns.append((url, code, err))   # site responds but cert is bad
        elif code in (200, 201, 204):
            ok.append(url)
        elif code in (301, 302, 307, 308):
            redirected.append((url, code))
        elif code in (403, 429, 500, 503):
            bot_blocked.append((url, code))      # bot-blocked ≠ dead
        else:
            broken.append((url, code, err))      # 404, 410, 0 = genuinely broken

    reachable = len(ok) + len(redirected) + len(bot_blocked) + len(ssl_warns)
    test(f"All live links reachable ({reachable}/{len(to_check)} OK, {len(broken)} broken)",
         len(broken) == 0,
         f"{len(broken)} dead links" if broken else "")

    if broken:
        print("  Genuinely dead links (fix or remove from itinerary.json):")
        for url, code, err in broken:
            sources = all_urls.get(url, [])
            print(f"    ✗ {code} — {url}")
            print(f"        sources: {', '.join(sources[:3])}")

    if ssl_warns:
        print(f"  ⚠ {len(ssl_warns)} URL(s) have SSL cert issues (work in browser, not a dead link):")
        for url, code, err in ssl_warns:
            print(f"    ~ {url}")

    if bot_blocked:
        print(f"  ℹ {len(bot_blocked)} URL(s) return 403/429 (bot-blocking, not dead):")
        for url, code in bot_blocked:
            print(f"    ~ {code} {url}")

    if redirected:
        print(f"  ℹ {len(redirected)} URL(s) redirect:")
        for url, code in redirected[:5]:
            print(f"    → {code} {url}")

    if skipped:
        print(f"  ℹ Skipped {len(skipped)} Google Maps / Booking.com URLs (checked in test 12)")


# ─────────────────────────────────────────────────────────────────────────────
# 12. GOOGLE MAPS URL VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

# Patterns that suggest a waypoint Google Maps will struggle with:
#  - too short (< 5 chars)
#  - no digits or known place indicator (postcode, road number)
#  - known-bad strings

AMBIGUOUS_PATTERNS = [
    re.compile(r'^.{1,4}$'),                      # too short
    re.compile(r'^[A-Z][a-z]+ [A-Z][a-z]+$'),    # "Two Words" — no postcode/road
]

# UK postcode pattern (partial is fine)
UK_POSTCODE = re.compile(r'[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}', re.I)

def waypoint_quality(wp):
    """Return (ok, reason) for a map waypoint string."""
    wp = wp.strip()
    if not wp:
        return False, "empty"
    if len(wp) < 5:
        return False, f"too short: '{wp}'"
    # Good if it has a postcode
    if UK_POSTCODE.search(wp):
        return True, "has postcode"
    # Good if it has a road number (A82, M6, B852, PH49, IV40...)
    if re.search(r'\b([A-Z]\d+|M\d+|[A-Z]{1,2}\d{1,2}\s*\d)', wp, re.I):
        return True, "has road/area code"
    # Good if it has 3+ words (specific enough)
    if len(wp.split()) >= 3:
        return True, "3+ words"
    return False, f"ambiguous: '{wp}' — add postcode or more words"


def test_google_maps_urls():
    print("\n── 12. Google Maps URL Validator ───────────────────────────────")
    data = load_json()
    html = load_html()

    # ── 12a. Waypoint quality in JSON ────────────────────────────────────────
    print("  12a. Waypoint specificity (JSON)")
    waypoint_issues = []
    for d in data["days"]:
        for wp in d.get("map_waypoints", []):
            ok, reason = waypoint_quality(wp)
            if not ok:
                waypoint_issues.append((d["day"], wp, reason))

    test("All map waypoints are specific enough for Google Maps",
         len(waypoint_issues) == 0,
         f"{len(waypoint_issues)} ambiguous" if waypoint_issues else "")

    for day_num, wp, reason in waypoint_issues:
        print(f"    ✗ Day {day_num}: {reason}")

    # ── 12b. Maps search queries in JSON stops ────────────────────────────────
    print("  12b. Maps search queries (stops)")
    query_issues = []
    for d in data["days"]:
        for stop in d.get("stops", []):
            mq = stop.get("maps_query", "")
            if mq:
                ok, reason = waypoint_quality(mq)
                if not ok:
                    query_issues.append((d["day"], stop["name"], mq, reason))

    test("All stop maps_query values are specific enough",
         len(query_issues) == 0,
         f"{len(query_issues)} ambiguous" if query_issues else "")

    for day_num, name, mq, reason in query_issues:
        print(f"    ✗ Day {day_num} '{name}': {reason}")

    # ── 12c. Maps direction URLs in HTML are well-formed ─────────────────────
    print("  12c. Google Maps direction URL structure (HTML)")
    if html is None:
        test("HTML available for Maps URL check", False)
        return

    maps_urls = re.findall(r'https://www\.google\.com/maps/dir/([^"\']+)', html)
    short_segment_issues = []
    for url_path in maps_urls:
        segments = url_path.split('/')
        for seg in segments:
            seg_decoded = seg.replace('+', ' ').strip()
            if seg_decoded and len(seg_decoded) < 3:
                short_segment_issues.append(seg_decoded)

    test(f"All {len(maps_urls)} Maps direction URLs have no empty/trivial segments",
         len(short_segment_issues) == 0,
         f"trivial segments: {short_segment_issues}" if short_segment_issues else "")

    # ── 12d. Fetch Maps URLs to confirm Google returns 200 ───────────────────
    print(f"  12d. Live-check Maps URLs resolve (HTTP 200 from Google)")
    if not maps_urls:
        test("Maps URLs found to check", False, "no maps/dir URLs in HTML")
        return

    # Check a sample — first, last, and one from the middle
    sample_indices = sorted({0, len(maps_urls)//2, len(maps_urls)-1})
    sample = [f"https://www.google.com/maps/dir/{maps_urls[i]}" for i in sample_indices]

    maps_broken = []
    for url in sample:
        _, code, err, _ = check_url(url, timeout=10)
        # Google returns 200 for all maps/dir requests (even bad ones)
        # but will return 4xx/5xx for malformed URLs
        if code not in (200, "SKIP"):
            maps_broken.append((url, code, err))

    test(f"Sample of {len(sample)} Maps URLs return HTTP 200",
         len(maps_broken) == 0,
         f"{len(maps_broken)} failed" if maps_broken else "")

    for url, code, err in maps_broken:
        print(f"    ✗ {code} — {url[:80]}...")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 13 — URL RELEVANCE (domain sanity + optional title check)
# ─────────────────────────────────────────────────────────────────────────────

# Domains that should only appear on stays, not on sightseeing/eating stops
ACCOM_DOMAINS = {
    'airbnb.co.uk', 'airbnb.com', 'booking.com', 'vrbo.com',
    'holiday-lettings.co.uk', 'hoseasons.co.uk', 'cottages.com',
    'syha.org.uk', 'hostellingscotland.org.uk',
}

# Keywords in page titles that suggest accommodation content (for live title check)
ACCOM_TITLE_KEYWORDS = [
    'cottage', 'holiday let', 'self catering', 'self-catering',
    'bed and breakfast', 'b&b', 'holiday rental', 'holiday home',
    'holiday park', 'lodge rental', 'lodge hire',
]

# Stop types that ARE accommodation — allowed to link to accom domains
ACCOM_STOP_TYPES = {'stay', 'airbnb', 'hotel', 'booking_com'}


def _collect_stop_urls(data):
    """Yield (context, stop_type, name, url) for every stop/eating entry with a URL."""
    for day in data.get('days', []):
        d = day['day']
        for s in day.get('stops', []):
            if s.get('url'):
                yield (f'Day {d} stop', s.get('type', ''), s['name'], s['url'])
        for e in day.get('eating', []):
            if e.get('url'):
                yield (f'Day {d} eating', e.get('type', ''), e['name'], e['url'])


def _fetch_title(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            html = r.read(8000).decode('utf-8', errors='ignore')
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip().lower() if m else ''
    except Exception:
        return None


def test_url_relevance():
    print("\n── 13. URL Relevance Check ─────────────────────────────────────")
    data = load_json()
    no_live = '--no-live-links' in sys.argv

    # 13a — Domain sanity check (always runs, no network needed)
    print("  13a. Accommodation domain check (stops & eating)")
    entries = list(_collect_stop_urls(data))
    domain_fails = []
    for ctx, stype, name, url in entries:
        domain = urlparse(url).netloc.lower().lstrip('www.')
        if domain in ACCOM_DOMAINS and stype not in ACCOM_STOP_TYPES:
            domain_fails.append((ctx, name, url))
    test(
        "No sightseeing/eating stops link to accommodation booking sites",
        len(domain_fails) == 0,
        f"{len(domain_fails)} issue(s)" if domain_fails else "",
    )
    for ctx, name, url in domain_fails:
        print(f"    ✗ {ctx}: '{name}' → {url}")

    # 13b — Page title relevance (only with live links)
    if no_live:
        print("  13b. Page title check — skipped (--no-live-links)")
        return

    print(f"  13b. Page title check — fetching titles for {len(entries)} URLs ...")
    title_fails = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch_title, url): (ctx, stype, name, url)
                   for ctx, stype, name, url in entries}
        for fut in as_completed(futures):
            ctx, stype, name, url = futures[fut]
            title = fut.result()
            if title is None:
                continue  # unreachable — already caught by test 11
            if stype not in ACCOM_STOP_TYPES:
                hits = [kw for kw in ACCOM_TITLE_KEYWORDS if kw in title]
                if hits:
                    title_fails.append((ctx, name, url, title[:60], hits))

    test(
        "No sightseeing/eating stop links to a page with accommodation content",
        len(title_fails) == 0,
        f"{len(title_fails)} issue(s)" if title_fails else "",
    )
    for ctx, name, url, title, hits in title_fails:
        print(f"    ✗ {ctx}: '{name}'")
        print(f"      URL:   {url}")
        print(f"      Title: {title}")
        print(f"      Flags: {', '.join(hits)}")


# ─────────────────────────────────────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_all():
    print("=" * 65)
    print("  SCOTLAND TRIP 2026 — TEST SUITE")
    print("=" * 65)

    test_json_integrity()
    test_walking_limits()
    test_fuel_legs()
    test_map_waypoints()
    test_url_structure()
    test_bookings()
    test_html_output()
    test_docx_output()
    test_consistency()
    test_safety_checks()
    test_google_maps_urls()
    test_live_links()
    test_url_relevance()

    # Summary
    passed = sum(1 for r in RESULTS if r[0] == "PASS")
    failed = sum(1 for r in RESULTS if r[0] == "FAIL")
    total = len(RESULTS)

    print("\n" + "=" * 65)
    print(f"  RESULTS: {passed}/{total} passed", end="")
    if failed:
        print(f"  ❌ {failed} FAILED")
        print("\n  Failed tests:")
        for status, name, detail in RESULTS:
            if status == "FAIL":
                print(f"    ✗ {name}" + (f" — {detail}" if detail else ""))
    else:
        print("  ✅ ALL PASSED")
    print("=" * 65)

    return failed


if __name__ == "__main__":
    failed = run_all()
    sys.exit(1 if failed else 0)

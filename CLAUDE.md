# Trip Planner — Claude Code Project

## What this project does

Generates per-trip output files from a per-trip JSON data source:

1. `trips/<trip-id>/output/<Trip>.docx` — full Word document itinerary
2. `trips/<trip-id>/output/index.html` — mobile-optimised iPhone/CarPlay route guide

Each trip is self-contained under `trips/<trip-id>/`. Builders and tests accept a `--trip` argument.

**GitHub Pages:** each trip deploys to `https://underyoureyes.github.io/trip-planner/<trip-id>/`

---

## Project structure

```
trip-planner/
├── CLAUDE.md                  ← you are here
├── docs/
│   ├── scotland-2026.md       ← Scotland trip reference
│   └── lake-garda-2026.md     ← Lake Garda trip reference
├── trips/
│   ├── scotland-2026/
│   │   ├── data.json          ← ALL Scotland trip data — edit to change anything
│   │   └── output/
│   │       ├── Scotland_Itinerary_2026.docx
│   │       └── index.html
│   └── lake-garda-2026/
│       ├── data.json          ← ALL Lake Garda trip data — edit to change anything
│       └── output/
│           └── index.html     ← HTML only (no Word doc for this trip)
├── builders/
│   └── build_html.py          ← Python script generating the HTML (--trip <id>)
├── tests/
│   └── test_all.py            ← test suite (--trip <id>)
└── assets/
    └── styles.css             ← shared colour tokens (reference only)
```

---

## Trips

| Trip | Dates | Live guide | Docs |
|---|---|---|---|
| Scotland 2026 | 23 May – 7 Jun 2026 | [Open](https://underyoureyes.github.io/trip-planner/scotland-2026/) | [docs/scotland-2026.md](docs/scotland-2026.md) |
| Lake Garda 2026 | 31 Aug – 7 Sep 2026 | [Open](https://underyoureyes.github.io/trip-planner/lake-garda-2026/) | [docs/lake-garda-2026.md](docs/lake-garda-2026.md) |

---

## Setup

```bash
# Python 3.9+
pip install pytest docx2txt
```

---

## Build, test and deploy

```bash
# Build HTML for a trip
python builders/build_html.py --trip scotland-2026

# Run tests
python tests/test_all.py --trip scotland-2026 --no-live-links

# Deploy to GitHub Pages
./deploy.sh scotland-2026
./deploy.sh lake-garda-2026
```

---

## Data model — data.json

### trip
Top-level metadata: `title`, `subtitle`, `travellers`, `dogs[]` (name, age, max_walk_miles — empty array for dog-free trips), `car` (model, tank_range_miles), `home_postcode`.

### stays[]
One entry per accommodation. Fields: `id`, `name`, `location`, `nights`, `checkin`, `checkout`, `type` (airbnb/hotel/booking_com), `url`, `cost_gbp`.

### days[]
One entry per day. Required fields:
- `day`, `date`, `title`, `stay_id` (matches a stays.id — null for travel days)
- `leg_miles`, `leg_drive_hours`
- `total_walk_miles` — must not exceed most-constrained dog's limit (5.0 miles for Scotland)
- `flags[]` — optional: `highlight`, `golf`, `ebike`, `fuel_warning`, `train`, `ballot_action`
- `map_waypoints[]` — array of place strings for Google Maps (max 10)
- `stops[]` — each stop: `name`, `type`, `detail`, optional `cost`/`url`/`maps_query`/`walk_miles`/`book_ahead`
- `eating[]` — each entry: `name`, `type`, `price_tier`, `detail`, optional `url`/`maps_query`
- `notes[]` — plain string tips and warnings

### stop types

```
sightseeing           general sightseeing (no dogs required)
sightseeing_dogs      sightseeing with dogs
dog_walk / walk_dogs  walk with dogs
photo_stop            quick roadside photo stop
viewpoint             roadside viewpoint, minimal walking
supplies              shopping stop
fuel                  fill up car — generates amber warning box
lunch_fuel            combined lunch and fuel stop
ebike_optional        optional e-bike/road bike hire
golf                  golf round
distillery            whisky distillery visit
pub_dogs              dog-friendly pub
castle_dogs           castle visit, dogs in grounds
castle_dogs_optional  optional detour castle with dogs
cruise_dogs           boat trip with dogs
boat_dogs             boat trip with dogs (alias)
gondola_dogs          gondola/cable car with dogs
train_dogs            train journey with dogs
attraction_dogs       indoor attraction that allows dogs
attraction_no_dogs    indoor attraction, dogs stay at accommodation
tidal_warning         tide-dependent crossing — generates red warning box
afternoon_tea_no_dogs afternoon tea, dogs stay at accommodation
```

### Special day fields
- `golf{}` — course, holes, cost_gbp, hire_included, booking, url, dogs_welcome
- `afternoon_tea{}` — name, detail, cost, url
- `ballot_reminder{}` — action, deadline, url, detail
- `ebike{}` — for days with e-bike panels
- `weather_url` — per-day weather link (AccuWeather for international; BBC for UK)

---

## How to add a new stop

Find the day in `days[]`, add to `stops[]`:

```json
{
  "name": "Glencoe Visitor Centre",
  "type": "sightseeing_dogs",
  "detail": "Dog-friendly café and discovery trails outside. Museum inside.",
  "cost": "Free outside; museum ~£8pp",
  "url": "https://www.nts.org.uk/visit/places/glencoe",
  "maps_query": "Glencoe Visitor Centre PH49"
}
```

Update `total_walk_miles` if the stop adds walking.

---

## Test suite overview

`tests/test_all.py` covers 12 test groups:

1. **JSON integrity** — days sequential, stays valid, required fields
2. **Walking limits** — every day ≤ most-constrained dog's limit (skipped if no dogs)
3. **Fuel/range safety** — no leg exceeds car range
4. **Map waypoints** — 2–10 waypoints per day, no empty strings
5. **URL structure** — all URLs valid http/https
6. **Bookings completeness** — all required bookings defined with priority
7. **HTML output** — all day sections, nav tabs, map links, info panels
8. **Word doc output** — exists, correct size, all days present (Scotland only)
9. **JSON ↔ HTML consistency** — day titles and stay names match
10. **Critical safety** — Holy Island, Jacobite, Loch Ness RIB (Scotland only)
11. **Live link checker** — all URLs reachable (skipped with `--no-live-links`)
12. **Google Maps validator** — waypoints specific enough, Maps URLs resolve

---

## Builder behaviour with no dogs

When `trip.dogs` is an empty array:
- Dog chip hidden from hero
- Travellers line shows without dog names
- Walking stats icon: 🚶 (not 🐾)
- Activities section title: "📍 Activities" (not "🐾 With [names]")
- Walking limit test skipped

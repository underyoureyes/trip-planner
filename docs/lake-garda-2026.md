# Lake Garda 2026 — Trip Reference

**Live guide:** https://underyoureyes.github.io/trip-planner/lake-garda-2026/
**Data file:** `trips/lake-garda-2026/data.json`

---

## Trip overview

| | |
|---|---|
| **Dates** | 31 Aug – 7 Sep 2026 (8 days, 7 nights) |
| **Travellers** | David & Lesley (no dogs) |
| **Transport** | Riviera Travel coach tour — all daytime excursions with guide |
| **Output** | HTML only (no Word doc) |

## Flights

| | |
|---|---|
| **Outbound** | BA LHR 11:50 → VCE 15:05, 31 Aug |
| **Inbound** | BA VCE 14:20 → LHR 15:45, 7 Sep |
| **Passengers** | Mr & Mrs David Castledine (BA Groups booking) |

## Hotel

**Hotel Europa SkyPool & Panorama 4★**
Piazza Catena 13, Riva del Garda, TN, Italy
B&B basis — evenings are independent
https://www.hoteleuropariva.it/en/

## Coach excursions (all transport & guide provided)

| Day | Excursion |
|---|---|
| Day 2 | Sirmione & Scaligero Castle |
| Day 3 | Malcesine & Monte Baldo cable car |
| Day 5 | Limone sul Garda & west shore |
| Day 6 | Bardolino wine tasting & lake swim |
| Day 7 | Verona day trip |

## Free days

### Day 1 — Arrival afternoon (~16:30 onwards)
Gentle orientation walk along Lungolago to Piazza III Novembre. Aperitivo on the lakefront.

### Day 4 — Full free day (suggested plan)
- **Morning** (08:30–11:30): Road bike hire at CCT Bike Rental, Arco (3km from hotel, €8 taxi). Riva → Torbole → return, ~30km flat lakeside path, 2–3 hrs. Book online in advance: https://www.cctbikerental.com/rentals/garda-bike-rentals/
- **Afternoon**: Choice of:
  - Bastione fortress (panoramic lift or 20-min walk up through olive groves — free)
  - Cascata del Varone waterfall (3km, €8 taxi, €7pp entry) — https://www.cascata-varone.com/en/
  - Arco medieval town & castle ruins (3km, €8 taxi — free castle)
  - **Golf Bogliaco** (18-hole PAR 70, ~13 miles on west shore, taxi ~€35 each way) — https://www.golfbogliaco.com/en/

## Evening dining — Riva del Garda

All evenings have 3 options (€/€€/€€€). Key restaurants:

| Restaurant | Tier | Website | Notes |
|---|---|---|---|
| Al Volt, Via Fiume 73 | €€€ | https://www.ristorantealvolt.com/ | Michelin-selected. **Closed Mondays.** Book ahead. ~€65-80pp |
| Bastione Lounge & Restaurant | €€ | https://bastione.eu/ | At the fortress — panoramic lift or 20-min walk |
| La Berlera, Località Ceole | €€ | https://www.laberlera.it/en | ~3km from hotel (taxi ~€8) |
| Osteria Il Gallo, Piazza San Rocco 5 | €€ | https://www.osteriailgallo.com/ | Historic osteria since 1884 |

## Evening dining — Verona (Day 7)

| Restaurant | Tier | Website | Notes |
|---|---|---|---|
| Osteria al Duca, Via Arche Scaligere 2 | € | https://www.osteriaalduca.it/ | 13th-century house (Romeo's), horse meat & pasta |
| Trattoria Al Pompiere, Vicolo Regina d'Ungheria 5 | €€ | https://alpompiere.com/ | Michelin listed. Book ahead. ~€45-55pp |
| Ristorante Arche, Via Arche Scaligere 6 | €€€ | https://ristorantearche.it/ | Open since 1877. **Closed Mondays.** Book well ahead. ~€80-100pp |

## Key bookings to make

| Item | Priority | Status |
|---|---|---|
| Flights BA LHR↔VCE | 1 | Booked |
| Hotel Europa 7 nights | 1 | Booked |
| Monte Baldo cable car (Day 3) | 2 | Not booked — sells out in Sep |
| Al Volt restaurant | 3 | Not booked — email info@ristorantealvolt.com |
| Ristorante Arche Verona (Day 7) | 3 | Not booked |
| CCT Bike Rental Day 4 | 4 | Not booked — book online 3+ days ahead |
| Golf Bogliaco Day 4 (if playing) | 4 | Not booked |
| Verona Arena entry | 3 | Not booked (guide may arrange) |
| Cascata del Varone Day 4 | 4 | Walk-in OK |

## Evening transport

No car — use local taxis for restaurants outside walking distance.
- Within Riva del Garda old town: ~€5-8
- Arco (3km): ~€8-12 return
- Torbole (8km): ~€12-18 return
- Golf Bogliaco / La Berlera (~13 miles): ~€35 each way

Ask hotel reception to call a taxi. The **itTaxi** app works in larger towns.

## Weather

- Days based in Riva del Garda: AccuWeather https://www.accuweather.com/en/it/riva-del-garda/1705/weather-forecast/1705
- BBC Weather does not reliably serve Italian locations — use AccuWeather

## Notes for builder / tests

- `dogs: []` — no dogs. Builder suppresses dog chip, walking icon uses 🚶, activities section titled "📍 Activities"
- `car.tank_range_miles: 999` — dummy value for test compatibility (coach tour, no car)
- Word doc not generated for this trip — "Word doc exists" test failure is expected and ignored
- AccuWeather and Booking.com are skipped in the live link checker (bot-blocking)

## Build & deploy

```bash
python builders/build_html.py --trip lake-garda-2026
python tests/test_all.py --trip lake-garda-2026 --no-live-links
./deploy.sh lake-garda-2026
```

# Scotland 2026 — Trip Reference

**Live guide:** https://underyoureyes.github.io/trip-planner/scotland-2026/
**Data file:** `trips/scotland-2026/data.json`

---

## Trip overview

| | |
|---|---|
| **Dates** | 23 May – 7 June 2026 (16 days) |
| **Travellers** | David & Lesley + Koda (age 11) + Monty (age 2) |
| **Car** | BMW 530e Estate (PHEV, 3-pin charging cable) |
| **Home** | Pulloxhill, MK45 5HD |
| **Total accommodation** | 15 nights across 7 stays |
| **Total cost** | ~£3,281 accommodation + activities |

## Route

Pulloxhill → Gretna → Loch Lomond → Glencoe → Skye → Loch Ness → Edinburgh → York → Home

## Stays

| Stay | Nights | Type |
|---|---|---|
| Night 1 Gretna | 1 | Airbnb |
| Loch Lomond | 2 | Hotel |
| Glencoe / Fort William area | 3 | — |
| Isle of Skye | 3 | — |
| Loch Ness / Inverness area | 2 | — |
| Edinburgh | 3 | — |
| York | 1 | — |

## Constraints (enforced by tests)

| Constraint | Value | Reason |
|---|---|---|
| Max daily walk | 5.0 miles | Koda is 11 — senior dog |
| Car tank range | 300 miles | BMW 530e |
| EV overnight top-up | ~28 miles | 3-pin socket charging |
| Map waypoints per day | ≤ 10 | Google Maps URL limit |
| Jacobite bookings | 2 separate | 1 dog per booking rule |
| Loch Ness cruise | Standard only | RIB does not allow dogs |

## Key flags used in data.json

- `highlight` — major feature day
- `golf` — golf round (St Andrews Day 13)
- `ebike` — e-bike option available
- `fuel_warning` — sparse fuel stretch
- `train` — Fort William → Mallaig train day
- `ballot_action` — St Andrews ballot reminder

## Day 6 — Fort William / Mallaig train

- Glenfinnan Viaduct Viewpoint stop: park at NTS car park (£3), 10 min walk to elevated viewpoint. Leave by 11:30.
- **ScotRail**: 12:18 dep Fort William → arrive Mallaig ~14:10. Return 16:05 → back Fort William ~18:00.
- Off-peak return ~£13-15pp. Dogs free. Book at scotrail.co.uk or buy at station.
- Do NOT get off at intermediate stops.

## Day 13 — St Andrews golf

- Course: St Andrews (Old Course ballot or other course TBC)
- Book/ballot well in advance — see `ballot_reminder` field in data.json Day 10

## Critical safety checks (test group 10)

- Holy Island crossing — tide check required
- Jacobite steam train — separate bookings for each dog (1 dog per booking rule)
- Loch Ness cruise — Standard cruise only; RIB does not allow dogs

## Bike hire added (Days 3–14)

All major towns on the route have `ebike_optional` stops in `stops[]` pointing to local bike hire (road bike + e-bike). URLs use Google Maps search format (not direct shop URLs) to avoid dead-link failures.

## Deep fried Mars bar locations

- Day 6 Mallaig: Jaffy's Fish & Chips
- Day 9 Portree: local chip shop
- Day 13 St Andrews: Cromars
- Day 14 Edinburgh: Blue Lagoon

## Build & deploy

```bash
python builders/build_html.py --trip scotland-2026
python tests/test_all.py --trip scotland-2026
./deploy.sh scotland-2026
```

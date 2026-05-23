# Trip Planner App — One Pager

| | |
|---|---|
| **Document** | HLD-07 — Executive One Pager |
| **Version** | 1.0 · Draft · 2026-05-23 |

---

## What Is It?

A **private, invite-only iPhone web app** that takes the hard work out of planning road trips. Users fill in a form, Claude AI builds a full day-by-day itinerary, and the finished trip sits on everyone's iPhone home screen — no App Store, no subscriptions, free for all users.

Built for real trips: **Scotland 2026** and **Lake Garda 2026** are the first use cases.

---

## How It Works

```
Fill in trip form  →  Claude builds itinerary  →  Import hotel emails  →  Publish & share
     (5 min)              (streamed live)          (from Gmail, optional)    (link to group)
         ↓
   Everyone opens the link on their iPhone → taps Navigate → Google Maps opens
```

---

## Who Can Use It

| User Type | Access |
|---|---|
| **Full user** (has Claude API key) | Create trips, run AI generation, edit, publish, share |
| **Read-only user** (no API key) | View shared trips, navigate, read offline — no creation |
| **Admin** | All of the above + manage invite codes, users, health checks |

Registration is **invite-only**. No public sign-up. No App Store. Users add it to their iPhone home screen from Safari.

---

## Functional Requirements

### FR-01 — Authentication
- Email and password login; invite-code-only registration
- Secure sessions (JWT); automatic token refresh; rate-limited login

### FR-02 — User Setup
- Step-by-step wizard: Claude API key, Gmail connection (optional), home location, car details, dog profiles
- All steps skippable; completable later from settings

### FR-03 — Trip Creation
- Intake form: destination, dates, travellers, dogs (name + max walk distance), car (model + fuel range), accommodation type, budget, trip style, must-visit places, interests (golf, distilleries, castles, cycling, boat trips, beaches, etc.)
- Auto-saves as draft; pre-fills from user profile

### FR-04 — AI Trip Builder
- Claude API generates a complete day-by-day itinerary from the intake form
- Streams output in real time so user sees the trip building live
- User can refine in plain English ("add a distillery on day 4")
- Requires a Claude API key; without one the user is in read-only mode

### FR-05 — Gmail Integration *(optional)*
- OAuth connection to Gmail (read-only scope)
- Scans inbox for hotel and excursion confirmation emails
- Extracts: property name, address, check-in/out dates, confirmation number
- User reviews and confirms each extraction before it is saved
- No raw email content stored

### FR-06 — Navigation
- Every stop has a **Navigate** button → opens **Google Maps** first (if installed) — preferred for superior routing and live traffic
- Falls back to **Apple Maps** if Google Maps is not installed; final fallback to Google Maps web URL
- User can set a permanent map app preference in settings to skip auto-detection
- Per-day drive times, distances, and ⚠️ fuel warnings when leg approaches car range limit
- **"Route Day"** button builds a multi-stop route with all the day's stops, in order

### FR-07 — Trip View
- Day-by-day tab navigation, optimised for one-handed iPhone use
- Expandable stop cards: name, type icon, address, notes, Navigate button
- Eating suggestions and daily notes per day
- Offline reading — trips cached on device for use with no signal
- "Today" shortcut jumps to the current day during the trip

### FR-08 — Save & Share
- Trips saved as **draft** (editable) or **published** (locked, shareable)
- Publishing generates a unique shareable link
- Read-only recipients must be registered users
- Owner can see who has viewed the trip

### FR-09 — Admin Panel
- Generate and manage invite codes
- View user list; disable accounts; reset passwords
- API health checks: Claude, Gmail, Google Maps, database

### FR-10 — Read-Only Mode
- Users without a Claude API key see only "Trips shared with me"
- Full navigation, offline reading, and trip browsing available
- Adding an API key in settings immediately unlocks creation

### FR-11 — Validation & Testing *(critical)*
- All trip data validated against schema on every save
- **Links validated live** — broken URLs blocked at publish; inline ⚠️ warnings in editor
- **Map waypoints validated** against Google Maps Geocoding API — wrong or vague waypoints blocked at publish
- 17-group automated test suite mirrors the existing trip-planner tests; all must pass in CI before deployment
- Nightly re-check of all published trips for newly broken links

---

## Technical Summary

| Concern | Choice |
|---|---|
| **Platform** | Progressive Web App (PWA) — iPhone home screen, no App Store |
| **Frontend** | Next.js 14 + Tailwind CSS |
| **Backend** | Node.js API (REST, versioned `/api/v1/`) |
| **Database** | PostgreSQL + Redis |
| **Hosting** | Private VPS (Nginx + Let's Encrypt HTTPS) |
| **AI** | Claude API — user supplies their own key |
| **Email** | Gmail API — user connects their own account via OAuth |
| **Maps** | Google Maps (preferred, deep-link) → Apple Maps (fallback) → Google Maps web (final fallback); Google Maps API for route estimates |
| **Auth** | JWT + bcrypt; invite-only registration |

---

## Key Risks (Top 3)

| # | Risk | Mitigation |
|---|---|---|
| 1 | **Data loss** if server fails without backup | Daily automated database backup to off-site storage; monthly restore test |
| 2 | **Claude API costs** if operator pays | Each user brings their own API key — zero operator cost |
| 3 | **Gmail OAuth warning** ("app unverified") | Google allows up to 100 test users without full verification; document workaround for users |

---

## What It Is Not

- Not an App Store app (no Apple fees, no review process)
- Not a booking engine (it reads confirmations; it never makes bookings)
- Not a public product (invite-only; no advertising; no commercial feature set)
- Not dependent on GitHub (deployed to a private web server)

---

*Full design: HLD-00 through HLD-06 in the `trip-planner-app` repository.*
# Trip Planner Web Application — System Overview

| Field | Value |
|---|---|
| **Document ID** | HLD-01 |
| **Title** | System Overview |
| **Version** | 1.0 |
| **Status** | Draft |
| **Date** | 2026-05-23 |
| **Author** | TBD |

---

## 1. Purpose & Vision

The Trip Planner Web Application is a private, invite-only Progressive Web App designed to replace and extend a manual, file-based trip planning workflow. The existing system requires a technically capable person to edit JSON files and run a Python build script to produce static HTML itineraries for road trips. While effective for consuming itineraries on mobile, it requires development knowledge to create or update them and provides no dynamic features.

The new application automates and enriches the planning experience end-to-end:

- A non-technical user fills in a structured intake form describing where they want to go, when, with whom, and with what vehicle.
- An AI assistant (Claude) generates a complete, day-by-day itinerary in the application's native data format — including suggested stops, walks, eating spots, and notes.
- Confirmation emails for hotels and excursions (received in Gmail) can be parsed automatically, enriching the itinerary with real booking data without manual re-entry.
- The finished itinerary is stored on a private server, readable offline on iPhone, and shareable with other members of the travelling group.

The vision is a self-contained planning companion: from "we want to visit Scotland" to a fully-detailed, navigable trip guide on everyone's iPhone home screen, achieved with minimal manual effort and no technical knowledge.

The system is not a commercial product. It is built for a small group of friends and family who take road trips together in the UK and Europe. There are no subscriptions, no advertising, and no App Store presence required. The deployment target is a private VPS with HTTPS.

---

## 2. In-Scope Features

- **User authentication** — Email/password login with invite-code-based registration.
- **First-run setup wizard** — Guided onboarding to capture Claude API key, Gmail OAuth consent, home location, car details, and dog profiles.
- **Trip intake form** — Structured form capturing destination, dates, travellers, dog profiles, car model and fuel range, accommodation preferences, budget tier, and trip style.
- **AI trip builder** — Integration with the Claude API to generate a structured trip itinerary, streamed in real time with refinement support.
- **Gmail email parser** — OAuth-based scanning of the user's inbox to extract hotel and excursion booking confirmation details.
- **Navigation integration** — Per-stop and per-day deep-links to Google Maps (preferred) and Apple Maps (fallback) with drive time and fuel range warnings.
- **iPhone-optimised trip view** — Day-by-day tab navigation, expandable stop detail cards, offline reading via service worker cache.
- **Trip save and share** — Persistent server-side storage; publishable trips with shareable links readable by other registered users.
- **Read-only mode** — Users without a Claude API key can view and navigate shared trips.
- **Basic admin panel** — Invite code generation, user list, API health checks.
- **Progressive Web App** — Installable on iPhone home screen; offline reading of published trips via service worker.
- **Automated test suite** — 17 test groups mirroring the existing trip-planner test suite.

---

## 3. Out of Scope

| Out-of-Scope Item | Reason |
|---|---|
| Native iOS app (Swift/SwiftUI) | Requires Apple Developer account ($99/yr), App Store review, Xcode/Mac dev environment, and significantly higher development effort. PWA is sufficient. |
| Android native app | Not a target platform at this time. |
| Booking and payment processing | The app reads existing confirmation emails but never initiates bookings. |
| Public user registration | Invite-only. A public sign-up path would change the security model. |
| Full travel agency features | No flight search, pricing comparison, or real-time availability lookups. |
| Push notifications (v1) | Limited on iOS prior to 16.4. Deferred to v2. |
| Real-time collaborative editing | Sharing is read-only for recipients. |
| AI conversation memory across sessions | Each Claude API call is self-contained. |
| Outbound email (transactional) | Password reset is admin-mediated in v1. |

---

## 4. Target Users

- **Primary users:** A family group or close friend group of approximately 5–15 people who travel together on road trips in the UK and Europe.
- **Technical level:** Non-technical. The application must function entirely through the web UI.
- **Primary device:** iPhone. Desktop browsers are supported but are not the primary design target.
- **Usage pattern:** Occasional and seasonal. Trip planning happens weeks or months before departure.
- **Dog owners:** Dog-friendly stops, maximum walk distances, and dog-friendly accommodation are first-class concerns.
- **Read-only users:** Travelling companions without a Claude API key who want to view and navigate shared trips.
- **Admin user:** At least one technically capable user who manages the server and invite codes.

---

## 5. iPhone PWA Deployment Model

### Why PWA Rather Than a Native App?

| Factor | PWA | Native iOS App |
|---|---|---|
| App Store required | No | Yes |
| Apple Developer account | No | Yes ($99/yr) |
| Installation method | Safari → Share → Add to Home Screen | App Store download |
| Update delivery | Automatic (next visit) | User must update via App Store |
| Offline reading | Yes (service worker) | Yes |
| Push notifications | Limited (iOS 16.4+ only) | Full support |
| Suitability for this project | ✅ Appropriate | Not justified for this scale |

### iOS Version Requirements

The application targets iOS 16.4 and above. Users on iOS 15 or below can use the app in Safari but cannot install it to the home screen with full offline support.

### HTTPS Requirement

Service workers, the Web App Manifest, and secure cookie flags all require HTTPS. The server uses Let's Encrypt certificates, renewed automatically by certbot.

---

## 6. High-Level User Journey

1. **Receive invite.** Admin shares an invite code out-of-band.
2. **First visit.** User navigates to the app URL in Safari on iPhone.
3. **Add to home screen.** Safari share button → "Add to Home Screen".
4. **Register.** Name, email, password, invite code.
5. **Setup wizard — Step 1:** Confirm profile.
6. **Setup wizard — Step 2:** Paste Claude API key (or skip → read-only mode).
7. **Setup wizard — Step 3:** Connect Gmail (optional).
8. **Setup wizard — Step 4:** Home location, car details, dog profiles.
9. **Create trip.** Tap "New Trip", complete the intake form.
10. **AI generation.** Tap "Build with AI" — itinerary streams in real time.
11. **Refine.** Type plain-English requests to adjust the itinerary.
12. **Import emails (optional).** Tap "Import from Email" — select hotel confirmation emails to extract booking details.
13. **Review & edit.** Browse day by day; edit individual stops.
14. **Publish.** Tap "Publish" — trip is locked and a shareable link is generated.
15. **Share.** Tap "Share" — copy link or use iOS share sheet to send via iMessage.
16. **Recipients view.** Other registered users open the link and browse read-only.
17. **On the road.** App opens from home screen; trip loads offline. Tap "Navigate" on any stop → Google Maps opens with directions.

---

## 7. Key External Dependencies

| Dependency | Purpose | Who Owns It | Fallback |
|---|---|---|---|
| Claude API (Anthropic) | AI itinerary generation | User (own API key) | Manual entry; read-only mode |
| Gmail API (Google) | Reading confirmation emails | User (OAuth consent) | Manual data entry |
| Google Maps API | Drive time estimates | Application (server key) | Navigation deep-links still work |
| Google Maps deep-links | In-car navigation | Google (no key required) | Apple Maps fallback |
| Apple Maps deep-links | Navigation fallback | Apple (no key required) | Google Maps web URL |
| Let's Encrypt / certbot | TLS certificate | Application operator | Manual certificate renewal |
| VPS Provider | Hosting | Application operator | Restore from backup on new VPS |

---

## 8. Relationship to the Existing System

- **Inherits the same data schema.** `trip_data` stores JSON matching the existing `data.json` structure. Existing trips can be imported without transformation.
- **Does not retire the Python builder.** The Python builder continues to run in parallel as a fallback rendering path.
- **Cannot be deployed to GitHub Pages.** The new app has server-side requirements incompatible with static hosting.
- **Scotland 2026 and Lake Garda 2026** are the first planned test cases for the new system.

---

## 9. Success Criteria

| ID | Criterion |
|---|---|
| SC-01 | A non-technical user can register and complete the setup wizard without admin assistance. |
| SC-02 | A user with a Claude API key can generate a complete UK road trip itinerary in under 5 minutes. |
| SC-03 | A user with Gmail connected can import hotel confirmation details in under 3 taps. |
| SC-04 | The app installs to the iPhone home screen and opens in standalone mode from iOS 16.4+. |
| SC-05 | A published trip is readable in full offline on iPhone. |
| SC-06 | Tapping "Navigate" opens Google Maps (or Apple Maps as fallback) with the correct destination. |
| SC-07 | The Scotland 2026 and Lake Garda 2026 JSON files can be imported and viewed without modification. |
| SC-08 | All API keys and OAuth tokens are stored encrypted at rest and never visible in logs or API responses. |
| SC-09 | The application is reachable exclusively over HTTPS. |
| SC-10 | A published trip link can be opened by a different registered user who sees the full itinerary. |
| SC-11 | A read-only user (no API key) can view a shared trip and tap Navigate without any errors. |

---

*End of HLD-01*
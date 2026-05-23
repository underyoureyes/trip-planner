# Trip Planner Web Application — Master Design Index

| Field | Value |
|---|---|
| **Document ID** | HLD-00 |
| **Title** | Master Design Index |
| **Version** | 1.0 |
| **Status** | Draft |
| **Date** | 2026-05-23 |
| **Author** | TBD |

---

## Executive Summary

This document set describes the high-level design for a new dynamic web application that extends an existing static HTML trip planner. The application enables a small, invite-only group of users to plan, build, and share road-trip itineraries from their iPhones — without any technical knowledge, App Store installation, or subscription fee.

The core workflow is: a user fills in a short trip intake form (destination, dates, travellers, dogs, car), and the Claude AI API generates a complete, structured, day-by-day itinerary in the application's native data format. If the user has connected their Gmail account, the app can scan for hotel and excursion confirmation emails and extract booking details automatically. The finished itinerary is stored on a private server, viewable offline on iPhone as a Progressive Web App (PWA), and shareable with other registered users via a link.

The system is not a commercial product. It is built for a small group of friends and family and is free of charge to users. It is deployed on a self-hosted VPS with HTTPS — not on GitHub Pages. The design deliberately inherits the existing trip data schema (trips, stays, days, stops, eating, notes) from the Python-based static HTML builder that produced the Scotland 2026 and Lake Garda 2026 itineraries, ensuring backward compatibility and data portability.

---

## Document Register

| Doc ID | Filename | Title | Summary | Status | Version | Date |
|---|---|---|---|---|---|---|
| HLD-00 | `HLD-00-index.md` | Master Design Index | This document. Executive summary and register of all design documents. | Draft | 1.0 | 2026-05-23 |
| HLD-01 | `HLD-01-overview.md` | System Overview | Purpose, scope, out-of-scope, target users, iPhone PWA deployment model, high-level user journey, external dependencies, and success criteria. | Draft | 1.0 | 2026-05-23 |
| HLD-02 | `HLD-02-architecture.md` | Architecture & Tech Stack | System architecture diagram, recommended tech stack with rationale, component breakdown, API design principles, PWA requirements, environment configuration, and deployment pipeline. | Draft | 1.0 | 2026-05-23 |
| HLD-03 | `HLD-03-features.md` | Feature Specifications | Full feature catalogue (F-01 through F-11) with user stories, acceptance criteria, priorities, and external dependencies. Includes 17-group test suite specification. | Draft | 1.0 | 2026-05-23 |
| HLD-04 | `HLD-04-data-model.md` | Data Model | SQL table definitions, field-level descriptions, entity relationships, and the canonical trip data.json sub-schema as a reference type definition. | Draft | 1.0 | 2026-05-23 |
| HLD-05 | `HLD-05-security.md` | Security Design | Authentication security, API key storage, Gmail OAuth security, transport security, server hardening, GDPR considerations, secrets management, and vulnerability surface. | Draft | 1.0 | 2026-05-23 |
| HLD-06 | `HLD-06-risks-alternatives.md` | Risks & Alternatives | Risk register (R-01 through R-12) with likelihood/impact ratings and mitigations; detailed evaluation of six alternative architectural approaches with verdicts. | Draft | 1.0 | 2026-05-23 |
| HLD-07 | `HLD-07-one-pager.md` | Executive One Pager | Single-page summary with all functional requirements, technical summary, and top risks. Start here. | Draft | 1.0 | 2026-05-23 |

---

## Reading Order

For a first read, the recommended sequence is:

1. **HLD-07** — One-page summary. Start here.
2. **HLD-01** — Understand what the system is, who it is for, and what it must do.
3. **HLD-02** — Understand how it is built and deployed.
4. **HLD-03** — Understand the detailed feature requirements and test suite.
5. **HLD-04** — Understand how data is stored and structured.
6. **HLD-05** — Understand the security model.
7. **HLD-06** — Understand the risks and why this architecture was chosen over alternatives.

---

## Document Relationships

```
HLD-01 (Why & What — scope, users, success criteria)
    └── HLD-02 (How it is built — stack, architecture, deployment)
            ├── HLD-03 (What each feature does — user stories, acceptance criteria, tests)
            ├── HLD-04 (How data is structured — tables, schema, relationships)
            └── HLD-05 (How it is secured — auth, encryption, hardening)

HLD-06 (Risk register + alternative approaches evaluated)
  references all of the above

HLD-07 (One-page summary — references all)
```

---

## Scope Boundaries at a Glance

**In scope:** AI-assisted trip planning via Claude API, Gmail booking email extraction, iPhone PWA with offline reading, invite-only authentication, trip saving and sharing, per-stop navigation deep-links to Google Maps (preferred) and Apple Maps (fallback), basic admin panel, read-only mode for users without API keys, 17-group automated test suite.

**Out of scope:** Native iOS app, booking or payment processing, public user registration, full travel agency features, Android-native support, push notifications (v1), real-time collaborative editing.

---

## Key Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Frontend | Next.js 14 + Tailwind CSS | React ecosystem, PWA support via next-pwa, strong mobile UX |
| Backend | Node.js + Express | Single language stack; good Anthropic SDK support; low overhead for small user base |
| Database | PostgreSQL + Redis | Relational integrity for trips and users; Redis for session cache |
| Auth | JWT (15 min) + refresh token (7 day) + bcrypt + invite codes | Simple, secure, no external OAuth dependency for core login |
| Hosting | Single VPS + Nginx reverse proxy + Let's Encrypt | Full control, low cost, appropriate for invite-only group |
| AI generation | Claude API (user-supplied key) | User bears their own API cost; no platform billing complexity |
| Gmail access | OAuth 2.0 with gmail.readonly scope | Optional enrichment only; minimal permission footprint |
| Navigation | Google Maps deep-links (preferred) → Apple Maps (fallback) → Google Maps web | Best routing first; iPhone-native fallback; no API key required for deep-links |
| Deployment | git pull + pm2 restart (or Docker Compose) | Simple enough for a single operator; no CI/CD complexity needed at this scale |

---

## Glossary

| Term | Definition |
|---|---|
| PWA | Progressive Web App — a web application that can be installed on an iPhone home screen and supports offline access via service worker |
| VPS | Virtual Private Server — a rented Linux cloud server with root access (e.g. Hetzner, DigitalOcean, Linode) |
| Intake Form | The structured trip planning questionnaire a user fills in before AI generation runs |
| Trip Data Schema | The JSON structure (trip metadata, stays[], days[], stops[], eating[], notes[]) inherited from the existing static HTML system |
| Invite Code | A single-use alphanumeric code that permits a new user to create an account; generated by an admin |
| Claude API | Anthropic's REST API for language model completions, used to generate itinerary content from form data |
| Gmail Extraction | The process of reading user-selected confirmation emails and parsing structured booking data from them |
| Standalone Mode | PWA display mode where the app opens without browser chrome (address bar, navigation buttons) — requires "Add to Home Screen" on iOS |
| Published Trip | A trip that has been locked and had a shareable link generated; cannot be edited without unpublishing |
| Draft Trip | A trip still being built; not yet shared; editable by its owner |
| Read-Only User | A registered user without a Claude API key; can view and navigate shared trips but cannot create or edit trips |

---

*End of HLD-00*
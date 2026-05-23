# Trip Planner Web Application — Risks & Alternatives

| Field | Value |
|---|---|
| **Document ID** | HLD-06 |
| **Title** | Risks & Alternatives |
| **Version** | 1.0 |
| **Status** | Draft |
| **Date** | 2026-05-23 |
| **Author** | TBD |

---

## 1. Risk Register

| ID | Risk | Likelihood | Impact | Overall | Mitigation Summary |
|---|---|---|---|---|---|
| R-01 | iPhone PWA limitations (iOS restrictions) | M | M | **Medium** | Target iOS 16.4+; document workarounds |
| R-02 | Claude API costs & rate limits | M | H | **High** | User supplies own API key; add usage display |
| R-03 | Gmail OAuth "unverified app" warning | M | M | **Medium** | Use testing mode for <100 users; document workaround |
| R-04 | Self-hosted server maintenance burden | M | M | **Medium** | Docker; managed VPS; automated backups |
| R-05 | Data loss if VPS fails without backup | H (if unmitigated) | H | **Critical** | Daily pg_dump to off-site storage; test restores |
| R-06 | API key leakage / data breach | L | H | **High** | AES-256 at rest; HTTPS only; server-side only decryption |
| R-07 | User lockout (forgotten password) | M | M | **Medium** | Admin reset flow; backup admin account |
| R-08 | Trip data schema evolution | L | M | **Low** | schema_version field; migration scripts |
| R-09 | Gmail scope changes or token revocation | L | H | **Medium** | Graceful degradation; re-auth flow |
| R-10 | Scalability if user base grows beyond ~20 | L | L | **Low** | Architecture has headroom; revisit if needed |
| R-11 | Gmail API quota limits | M | M | **Medium** | Read-only scope limits exposure; cache parsed results |
| R-12 | Claude API deprecation or pricing changes | L | H | **Medium** | Decouple AI layer; swap provider if needed |

---

## 2. Alternative Approaches Summary

| Alternative | Verdict |
|---|---|
| A — Native iOS App (Swift) | ❌ Not recommended — $99/yr, App Store review, Xcode required |
| B — Flutter | ⚠️ Consider if Android support needed later |
| C — GitHub Pages (current approach) | ❌ Not feasible — cannot securely store API keys or user accounts |
| D — Vercel + Supabase | ✅ **Strong alternative** — zero server maintenance, free tiers |
| E — No-Code (Notion/Airtable) | ❌ Not suitable for the required feature set |
| F — Lightweight backend on existing repo | ⚠️ Good Phase 1 bridge — prove concept, then migrate |

---

## 3. Recommended Path Forward

**Phase 1 (2–4 weeks):** Use Vercel + Supabase for rapid prototyping. Build intake form → Claude API → display generated trip → basic auth. Validate with Scotland/Lake Garda re-creation.

**Phase 2 (4–8 weeks):** Add Gmail OAuth, trip save/share, PWA install, admin panel. Migrate to self-hosted VPS if data privacy is a priority.

**Phase 3 (ongoing):** Backup strategy, security hardening, user documentation.

> ⚠️ **Single most important risk:** R-05 (data loss). Backup strategy must be in place and tested before inviting any users.

> ✅ **Single biggest quick win:** Vercel + Supabase for Phase 1 — working prototype in days, not weeks.

*Full risk details and alternative evaluations: see HLD-06-risks-alternatives.md in the design-docs/ folder.*
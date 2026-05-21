# Feature 18 — User Traffic Dashboard

**Date:** 2026-05-21
**Status:** REQUIREMENTS — ready for implementation

---

## Goal

An ops-accessible traffic dashboard showing anonymised site usage metrics — total users, daily activity, and login trends. No personally identifiable information (PII) is exposed in the UI or API response. All aggregations happen server-side.

---

## Scope

| In scope | Out of scope |
|---|---|
| Login event logging on every Google OAuth sign-in | Individual user management (edit, delete, RBAC) |
| KPI summary tiles (totals, active by period) | Email addresses, names, or profile pictures in UI |
| Daily activity table (last 30 days) | Real-time / WebSocket updates |
| 30-day login trend chart | External analytics integrations |
| New page in Ops dashboard | Exporting / downloading data |

---

## Data Model Changes

### 1. New table — `login_events`

Logs one row per login event. Used for all time-series aggregations.

| Column | Type | Notes |
|---|---|---|
| `id` | String (UUID) | Primary key |
| `user_id` | String (FK → `users.id`) | Anonymised at API layer — never returned to UI |
| `logged_at` | DateTime (UTC) | Timestamp of the login |

### 2. New column — `users.first_login_date`

| Column | Type | Notes |
|---|---|---|
| `first_login_date` | DateTime (UTC) | Set once on first login, never updated — used for "new registrations per day" |

### 3. Auth callback changes (`api/v1/auth.py`)

On every successful Google OAuth login:
- Insert a row into `login_events` with the current UTC timestamp
- Set `users.first_login_date` if not already set (first-time users only)
- Existing `users.last_login_date` update unchanged

### 4. Alembic migration

New migration: `20260521_add_login_events`
- `CREATE TABLE login_events`
- `ALTER TABLE users ADD COLUMN first_login_date DATETIME`

---

## API

### Endpoint

```
GET /api/v1/experience/users/traffic
```

Protected by JWT. Returns aggregated traffic data only — no PII.

### Response schema

```json
{
  "summary": {
    "total_users": 12,
    "active_today": 3,
    "active_this_week": 7,
    "active_this_month": 11,
    "total_logins_all_time": 148
  },
  "daily": [
    {
      "date": "2026-05-21",
      "unique_users": 3,
      "total_logins": 7,
      "new_registrations": 1
    },
    {
      "date": "2026-05-20",
      "unique_users": 2,
      "total_logins": 4,
      "new_registrations": 0
    }
  ]
}
```

`daily` returns the last 30 days, ordered newest first.

### Location

New router file: `src/rita/api/experience/users.py`
Registered in `main.py` under the experience prefix.

---

## UI

### Page

New standalone page: `dashboard/users.html`
Accessible via a link in the Ops dashboard navigation.
Protected — redirects to login if no valid JWT.

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  User Traffic                          [last 30 days]   │
├──────────┬──────────┬──────────┬──────────┬────────────┤
│  Total   │  Active  │  Active  │  Active  │  Total     │
│  Users   │  Today   │ 7 Days   │ 30 Days  │  Logins    │
│   12     │    3     │    7     │   11     │   148      │
├─────────────────────────────────────────────────────────┤
│  Daily Logins — last 30 days  [bar chart]               │
│  ▁▂▃▅▄▃▂▁▂▃▅▆▅▄▃▂▃▄▅▄▃▂▁▂▃▄▅▆▅▄                        │
├──────────────────────────────────────────────────────────┤
│  Date        │ Unique Users │ Total Logins │ New Users  │
│  2026-05-21  │      3       │      7       │     1      │
│  2026-05-20  │      2       │      4       │     0      │
│  ...                                                     │
└──────────────────────────────────────────────────────────┘
```

### KPI Tiles (5 cards)
- Total Users
- Active Today
- Active This Week (7 days)
- Active This Month (30 days)
- Total Logins (all time)

### Trend Chart
- Bar chart — one bar per day, last 30 days
- Y-axis: total logins that day
- X-axis: date labels (show every 5th label to avoid crowding)
- Library: Chart.js (already used in the project)

### Daily Activity Table
- Columns: Date | Unique Users | Total Logins | New Registrations
- 30 rows (one per day), newest first
- No pagination needed (fixed 30-day window)
- No sorting or filtering required

### Access Control
- Page requires valid JWT (same as other dashboard pages)
- No additional RBAC gate for v1 — any authenticated user can view traffic stats
- (Future: restrict to `can_access_ops=True` if needed)

---

## File Checklist

| File | Change |
|---|---|
| `src/rita/models/login_event.py` | New ORM model |
| `src/rita/models/__init__.py` | Import LoginEventModel |
| `src/rita/models/user.py` | Add `first_login_date` column |
| `alembic/versions/20260521_add_login_events.py` | New migration |
| `src/rita/api/v1/auth.py` | Log event + set first_login_date on callback |
| `src/rita/repositories/login_event.py` | New repository |
| `src/rita/api/experience/users.py` | New experience router |
| `src/rita/main.py` | Register new router |
| `dashboard/users.html` | New page |
| `dashboard/js/users/main.js` | Page JS — fetch, render KPIs + chart + table |

---

## Definition of Done

- [ ] `login_events` table created via Alembic migration
- [ ] Every Google OAuth login inserts a `login_events` row
- [ ] `GET /api/v1/experience/users/traffic` returns correct aggregated data
- [ ] `dashboard/users.html` renders KPIs, chart, and table from the API
- [ ] No email, name, or any PII appears in API response or UI
- [ ] Page redirects to login if JWT is missing
- [ ] Existing auth tests still pass

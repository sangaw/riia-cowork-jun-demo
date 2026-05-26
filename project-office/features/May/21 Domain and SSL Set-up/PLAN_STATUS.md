# Feature 17 — Domain and SSL Set-up

**Date started:** 2026-05-21
**Status:** COMPLETE — `https://riia.ravionics.nl` live with Cloudflare SSL

---

## Goal

Expose RITA production site at `https://riia.ravionics.nl` with valid SSL certificate, replacing the raw EC2 public IP address.

---

## Final Infrastructure State

| Item | Value |
|---|---|
| EC2 Elastic IP | `34.239.207.17` |
| Domain registrar | Strato (Netherlands) |
| DNS provider | Cloudflare (free plan) — ACTIVE |
| Nameservers | `conrad.ns.cloudflare.com` / `crystal.ns.cloudflare.com` |
| RITA URL | `https://riia.ravionics.nl` ✅ |
| SSL method | Cloudflare proxy (orange cloud) — free, no certbot needed |
| Cloudflare SSL mode | Flexible (Cloudflare→EC2 over HTTP, browser→Cloudflare over HTTPS) |
| Nginx on EC2 | HTTP only on port 80, proxies to localhost:8000 |

---

## What Was Done

- [x] Nginx installed on EC2 (also now baked into Terraform cloud-init — see Feature 15)
- [x] Certbot installed on EC2 (ultimately not used — Cloudflare SSL used instead)
- [x] EC2 security group: ports 80 and 443 open
- [x] Cloudflare account created, `ravionics.nl` added
- [x] Cloudflare auto-imported all existing Strato DNS records
- [x] Strato nameservers updated to Cloudflare nameservers
- [x] DNS propagation confirmed
- [x] `riia` A record added in Cloudflare → `34.239.207.17`, **Proxied (orange cloud)**
- [x] `ravionics.nl` and `www` A/AAAA records set to **DNS only** (grey cloud)
- [x] SSL/TLS mode set to **Flexible** in Cloudflare
- [x] `https://riia.ravionics.nl` confirmed working end-to-end

---

## Remaining Steps (future session)

- [ ] Update GitHub secret `RITA_BASE_URL` from `http://34.239.207.17` to `https://riia.ravionics.nl`
- [ ] Update Google OAuth Console → add `https://riia.ravionics.nl/auth/callback` to redirect URIs
- [ ] Trigger redeploy to pick up new `RITA_BASE_URL`
- [ ] Update `SPEC_Prod_Deploy.md` to document nginx + Cloudflare SSL layer
- [ ] Update `production.yaml` `cors_origins` to `https://riia.ravionics.nl`

---

## DNS Records — Cloudflare (final state, do not delete)

| Type | Name | Value | Proxy |
|---|---|---|---|
| A | `riia` | `34.239.207.17` | **Proxied (orange)** — RITA, Cloudflare handles SSL |
| A | `ravionics.nl` | `212.227.172.254` | DNS only (grey) — Strato main site |
| A | `www` | `217.160.0.119` | DNS only (grey) — Strato main site |
| AAAA | `ravionics.nl` | `2001:8d8:105:1:0:1:0:2` | DNS only (grey) |
| AAAA | `www` | `2001:8d8:100f:f000::200` | DNS only (grey) |
| MX | `ravionics.nl` | `smtp.rzone.de` | DNS only |
| TXT | `_dmarc` | `v=DMARC1;p=reject;` | DNS only |

**Do not touch MX, TXT, SRV, CNAME records** — these are Strato email infrastructure.
**Do not proxy ravionics.nl or www A/AAAA records** — breaks the Strato-hosted main site.

---

## Lessons Learned

### Why certbot failed initially
Let's Encrypt HTTP-01 challenge reached `riia.ravionics.nl` via IPv6 (`2001:8d8:100f:f000::200`).
Strato had auto-created an AAAA record for `riia` pointing to their servers, not EC2.
Strato returned HTTP 204, failing the challenge.
Fix: migrated DNS to Cloudflare (full record control), removed Strato AAAA for `riia`.

### Why Cloudflare SSL is better than certbot here
- No certificate renewal management (Cloudflare auto-renews)
- No nginx TLS config required — origin stays plain HTTP
- Free on Cloudflare's free plan
- Certbot still needs DNS to be grey cloud during issuance — extra complexity

### Why ravionics.nl went down during migration
Cloudflare auto-imported the `ravionics.nl` and `www` records as **Proxied**.
Cloudflare then tried to apply its own SSL handling to Strato-hosted pages.
With SSL mode not yet configured, this broke the main site.
Fix: set `ravionics.nl` and `www` A/AAAA records to **DNS only** (grey cloud).
Rule: only proxy records for services YOU control the origin server of.

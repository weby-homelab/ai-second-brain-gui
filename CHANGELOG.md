# Changelog

## 0.7.1 — 2026-08-19

### Fixed

- Aligned note apply, DecisionService, completion evidence, read-only mutation guards and POWER 3.6.3 pin.
- Downgraded unsupported A2A wording to experimental custom discovery.


## 0.7.0 — 2026-08-15

### Security

- Enabled secure session/CSRF cookies by default and made session lifetime configurable.
- Added HSTS, `Permissions-Policy`, and `Cache-Control: no-store` response headers.
- Added early request-size enforcement and bounds for search, note, task, and SSE inputs.
- Added CSRF validation to logout.
- Bounded SSE lifetime and concurrency, added disconnect handling, heartbeat, and no-buffering headers.
- Pinned the Python base image and `power-framework` to reviewed immutable revisions.
- Hardened the Compose deployment with loopback-only publishing and explicit resource limits.

### UI

- Moved shared inline JavaScript into the CSP-compatible static application bundle.
- Added keyboard focus restoration and `inert` handling for the mobile navigation drawer.
- Removed the inline graph event handler blocked by the strict CSP.

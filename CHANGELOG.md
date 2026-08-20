# Changelog

## 0.7.4 — 2026-08-20

### Release

- Patch release from the final POWER 3.6.5-aligned mainline: immutable image
  readback naming, live Docker E2E fixture permissions, and release metadata are
  consistent for the published tag. Docker digest and live E2E receipt are recorded
  in `compatibility.json`.

## 0.7.3 — 2026-08-20

### Contract and Security

- Aligned the GUI candidate with immutable POWER `v3.6.5` `power.application.v2`; final publication evidence is recorded by the subsequent `0.7.4` release.
- Offloaded blocking POWER calls through a bounded worker limiter, including bounded SSE polling.
- Added redacted typed errors with request correlation IDs; stable A2A and multi-writer Federation remain unsupported.

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

# POWER-GUI 0.7.10

POWER-GUI 0.7.10 is the corrective GUI half of the POWER 3.7.4 Suite
candidate. It binds `power-framework==3.7.4`, the `power.application.v2`
schema, and the shared exact dependency constraints.

POWER 3.7.4 replaces moved populated virtual environments with unique
final-location release slots. The managed `current` pointer is switched only
after exact artifact and launcher verification, the previous release slot is
retained for rollback, and legacy populated venvs are preserved.

The release workflow publishes the wheel, sdist, SPDX SBOM, provenance
attestation, and hash-bound receipt. The Docker workflow builds the exact
source-bound pair as a non-root, read-only multi-architecture image and reads
back its immutable digest.

This note does not claim publication or Suite Stable status before signed-tag,
artifact, native GUI, MCP, container, and public readback gates pass. Local
synthetic tests or a disposable vault do not constitute a real-vault quality
or human-quality claim; human-quality evidence remains sealed.

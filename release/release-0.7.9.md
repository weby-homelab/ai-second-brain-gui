# POWER-GUI 0.7.9

POWER-GUI 0.7.9 is the corrective GUI half of the POWER 3.7.3 suite. It
consumes the shared exact dependency constraints and pins POWER core to the
signed source commit `925f490aefbffff72ed92fd736210262ed445160`.

The patch follows the public POWER `v3.7.2` Skill-tree B4/Stage 7 blocker:
installed Python bytecode caches made the packaged Skill file set and hash
depend on the local installation state. POWER `v3.7.3` excludes generated
`__pycache__` and `.pyc` files from all Skill tree walks and adds regression
coverage, while the GUI pair is rebuilt against that exact core.

The release workflow publishes the wheel, sdist, SPDX SBOM, provenance
attestation, and hash-bound receipt. The Docker workflow verifies the shared
constraints digest, publishes the multi-arch image, reads back its immutable
digest, and runs live E2E.

Local synthetic tests or a disposable vault do not constitute a real-vault quality or human-quality claim. Human-quality evidence remains sealed and is not inferred from technical test counts.

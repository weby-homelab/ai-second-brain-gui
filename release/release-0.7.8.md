# POWER-GUI 0.7.8

POWER-GUI 0.7.8 is the corrective GUI half of the POWER 3.7.2 suite. It
consumes the shared exact dependency constraints and pins POWER core to the
signed source commit `a70ecbba880a3e9d13e7cdac3b729987169a8d13`.

The patch follows the immutable POWER `v3.7.1` native-bootstrap NO-GO: the
paired release uses the corrected core installer that rewrites staged Python
console shims when managed paths contain spaces or Unicode characters.

The release workflow publishes the wheel, sdist, SPDX SBOM, provenance
attestation, and hash-bound receipt. The Docker workflow verifies the shared
constraints digest, publishes the multi-arch image, reads back its immutable
digest, and runs live E2E.

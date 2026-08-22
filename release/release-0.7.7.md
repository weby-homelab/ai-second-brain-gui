# POWER-GUI 0.7.7

POWER-GUI 0.7.7 is the constraints-bound GUI half of the POWER 3.7.1 suite.
It consumes the shared exact dependency constraints and pins POWER core to
signed source commit `8e172b82b98c8980a83e433744ea2ed6cdedce82`.

The release workflow publishes the wheel, sdist, SPDX SBOM, provenance
attestation, and hash-bound receipt. The Docker workflow verifies the shared
constraints digest, publishes the multi-arch image, reads back its immutable
digest, and runs live E2E.

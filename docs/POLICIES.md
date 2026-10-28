<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Toolchain policy

Python 3.11 is the floor (`python = ">=3.11,<4.0"` in `pyproject.toml`),
with Linux CI on 3.11, 3.12, 3.13 and 3.14. The container image runs
3.14. Raising the floor is a maintainer decision, recorded in the changelog.
The floor moved from 3.10 to 3.11 because the test toolchain no longer
resolves on 3.10 (Hypothesis 6.170.12 needs 3.11), and the whole
`acmt001` suite moved to 3.11 with it in 0.0.14. No distro-system
Python is supported.

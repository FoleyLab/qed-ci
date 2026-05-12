# QED-CI
An open-source package to simulate strongly correlated molecules coupled to quantized cavity modes.

## Features

- Supports restricted references at the RHF or CQED-RHF levels, where the coherent state transformation is used for CQED-RHF
- Supports correlated levels including: QED-FCI, QED-CASCI, SA-QED-CASSCF
- Supports analytic gradients for ground- and excited- (polariton) states at the SA-QED-CASSCF level

Within the `src/` directory (source-only):

- helper_cqed_rhf.py provides restricted hartree fock for the Pauli-Fierz Hamiltonian in the coherent state basis
- helper_PFCI.py provides helper functions for arbitrary CI with Pauli-Fierz Hamiltonian
- gmres.py, residual_minimization.py, ortho_script.py, and nuclear_grad.py provide supporting numerical routines

Example workflows and run scripts now live in `examples/`.


## Getting Started
**0.  Clone repo** 

**1.  Install psi4** 

Using Conda (easy option):
- conda install psi4 python=3.10 -c conda-forge

or

From source (harder option):
- Follow directions [here](https://psicode.org/installs/v191/)

**2. Install numba and pytest:**
- pip install numba pytest

Note other python dependencies should be installed if you used the Conda option.  Other dependencies include numpy and scipy.

**3. Build the native C helpers**

See `BUILDING.md` for Linux/Intel and macOS/Apple Silicon options.

Quick examples:
- `make`
- `make CC=icx`
- `make CC=clang BLAS=accelerate`

**4. Run tests** 
- From the repository root (`qed-ci/`), run `pytest -v tests/`

# Building native C helpers

The project ships C extensions in `src/ci_solver.c` and `src/orbital.c` that build into `src/cfunctions.so`.

## Quick start

```bash
pip install numba
make
```

Use `make show-config` to inspect detected compiler/backend/include/lib flags.

## Linux + Intel oneAPI (MKL)

Activate your environment first (example from your setup):

```bash
conda activate p4dev
```

If oneAPI is installed system-wide, source the oneAPI environment before building:

```bash
source /opt/intel/oneapi/setvars.sh
```

Then build with Intel compiler and MKL:

```bash
make clean
make CC=icx BACKEND=mkl
```

### If `#include <mkl.h>` is not found

MKL headers are often inside either:
- `$MKLROOT/include` (oneAPI installs), or
- `$CONDA_PREFIX/include` (conda installs; with `p4dev`, this is that env path while activated).

You can find them with:

```bash
find "$CONDA_PREFIX" -name mkl.h 2>/dev/null
find "$CONDA_PREFIX" -name mkl_lapacke.h 2>/dev/null
```

If needed, set `MKLROOT` explicitly:

```bash
make clean
make CC=icx BACKEND=mkl MKLROOT=/path/to/mkl
```

## macOS Apple Silicon

### Option A: Accelerate (built-in)

```bash
make clean
make CC=clang BACKEND=accelerate
```

### Option B: OpenBLAS

```bash
brew install openblas
make clean
make CC=clang BACKEND=openblas OPENBLAS_PREFIX=/opt/homebrew/opt/openblas
```

If you need OpenMP on macOS:

```bash
brew install libomp
make clean
make CC=clang BACKEND=accelerate OPENMP=1
```

## Notes

- Default backend is `mkl` on Linux and `accelerate` on macOS.
- Default compiler is `cc`; override with `CC=icx`, `CC=clang`, or `CC=gcc`.
- `make clean` removes object files and `src/cfunctions.so`.

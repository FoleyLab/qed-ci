# Building native C helpers

The project ships C extensions in `src/ci_solver.c` and `src/orbital.c` that build into `src/cfunctions.so`.

## Quick start

```bash
pip install numba
make
```

## Linux + Intel oneAPI

Use Intel compiler and OpenMP:

```bash
make clean
make CC=icx
```

This maps to your current workflow (`icx ... -qopenmp ...`).

## macOS Apple Silicon

### Option A: Accelerate (built-in)

```bash
make clean
make CC=clang BLAS=accelerate
```

### Option B: OpenBLAS

```bash
brew install openblas
make clean
make CC=clang OPENBLAS_PREFIX=/opt/homebrew/opt/openblas
```

If you need OpenMP on macOS:

```bash
brew install libomp
make clean
make CC=clang BLAS=accelerate OPENMP=1
```

## Notes

- `BLAS=accelerate` is only relevant on macOS.
- Default compiler is `cc`; override with `CC=icx`, `CC=clang`, or `CC=gcc`.
- `make clean` removes object files and `src/cfunctions.so`.

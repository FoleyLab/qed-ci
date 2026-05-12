CC ?= cc
CFLAGS ?= -fPIC -O3 -Wall -Wextra
CPPFLAGS ?=
LDFLAGS ?=
LDLIBS ?=
SRC = src/ci_solver.c src/orbital.c
OBJ = $(SRC:.c=.o)
SHLIB = src/cfunctions.so

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

# --- BLAS/LAPACK backend selection ---
# BACKEND options:
#   mkl (default on Linux) | accelerate (macOS) | openblas
BACKEND ?=

ifeq ($(strip $(BACKEND)),)
  ifeq ($(UNAME_S),Darwin)
    BACKEND := accelerate
  else
    BACKEND := mkl
  endif
endif

# --- OpenMP flags ---
ifeq ($(CC),icx)
  CFLAGS += -qopenmp
  LDFLAGS += -qopenmp
endif

ifeq ($(OPENMP),1)
  ifeq ($(CC),clang)
    CFLAGS += -Xpreprocessor -fopenmp
  else
    CFLAGS += -fopenmp
  endif
  LDLIBS += -lomp
endif

# --- Backend-specific flags ---
ifeq ($(BACKEND),mkl)
  # Prefer explicit MKLROOT; fallback to CONDA_PREFIX for conda MKL installs.
  ifneq ($(MKLROOT),)
    CPPFLAGS += -I$(MKLROOT)/include
    LDFLAGS += -L$(MKLROOT)/lib -L$(MKLROOT)/lib/intel64
  endif
  ifneq ($(CONDA_PREFIX),)
    CPPFLAGS += -I$(CONDA_PREFIX)/include
    LDFLAGS += -L$(CONDA_PREFIX)/lib
  endif
  LDLIBS += -lmkl_rt -lpthread -lm -ldl
endif

ifeq ($(BACKEND),accelerate)
  LDLIBS += -framework Accelerate
endif

ifeq ($(BACKEND),openblas)
  LDLIBS += -lopenblas
  ifneq ($(OPENBLAS_PREFIX),)
    CPPFLAGS += -I$(OPENBLAS_PREFIX)/include
    LDFLAGS += -L$(OPENBLAS_PREFIX)/lib
  endif
endif

all: $(SHLIB)

$(SHLIB): $(OBJ)
	$(CC) -shared -o $@ $^ $(LDFLAGS) $(LDLIBS)

%.o: %.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

clean:
	rm -f src/*.o $(SHLIB)

show-config:
	@echo "CC=$(CC)"
	@echo "BACKEND=$(BACKEND)"
	@echo "MKLROOT=$(MKLROOT)"
	@echo "CONDA_PREFIX=$(CONDA_PREFIX)"
	@echo "CPPFLAGS=$(CPPFLAGS)"
	@echo "CFLAGS=$(CFLAGS)"
	@echo "LDFLAGS=$(LDFLAGS)"
	@echo "LDLIBS=$(LDLIBS)"

.PHONY: all clean show-config

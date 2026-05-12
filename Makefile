CC ?= cc
CFLAGS ?= -fPIC -O3 -Wall -Wextra
SRC = src/ci_solver.c src/orbital.c
OBJ = $(SRC:.c=.o)
SHLIB = src/cfunctions.so

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

ifeq ($(CC),icx)
  CFLAGS += -qopenmp
  LDFLAGS += -qopenmp
endif

ifeq ($(UNAME_S),Darwin)
  ifeq ($(UNAME_M),arm64)
    ifeq ($(BLAS),accelerate)
      LDLIBS += -framework Accelerate
    else
      LDLIBS += -lopenblas
      ifneq ($(OPENBLAS_PREFIX),)
        CFLAGS += -I$(OPENBLAS_PREFIX)/include
        LDFLAGS += -L$(OPENBLAS_PREFIX)/lib
      endif
    endif
    ifeq ($(OPENMP),1)
      CFLAGS += -Xpreprocessor -fopenmp
      LDLIBS += -lomp
    endif
  endif
endif

all: $(SHLIB)

$(SHLIB): $(OBJ)
	$(CC) -shared -o $@ $^ $(LDFLAGS) $(LDLIBS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f src/*.o $(SHLIB)

.PHONY: all clean

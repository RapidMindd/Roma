ifeq ($(shell uname -s),Darwin)
CXX = g++-16
else
CXX = g++
endif
PYTHON ?= python3
BASE = -std=c++17 -Wall -Wextra -Wpedantic -Wno-unused-function -fPIC -ffp-contract=off
NOVEC = -fno-tree-vectorize -fno-tree-slp-vectorize
OPT = -O3 -march=native
VARIANTS = scalar_o0 scalar_o3 simd_o0 simd_o3
LIBS = $(addprefix build/libgaussian_blur_,$(addsuffix .so,$(VARIANTS)))

.PHONY: all test clean
all: $(LIBS) build/libgaussian_blur.so

build:
	mkdir -p build

build/libgaussian_blur_scalar_o0.so: FLAGS = -O0 $(NOVEC)
build/libgaussian_blur_scalar_o3.so: FLAGS = $(OPT) $(NOVEC)
build/libgaussian_blur_simd_o0.so: FLAGS = -O0 -DVECTOR=1
build/libgaussian_blur_simd_o3.so: FLAGS = $(OPT) -ftree-vectorize -DVECTOR=1

$(LIBS): src/gaussian_blur.cpp src/gaussian_blur.h Makefile | build
	$(CXX) $(BASE) $(FLAGS) -shared $< -o $@

build/libgaussian_blur.so: build/libgaussian_blur_simd_o3.so
	cp $< $@

build/test_%: tests/test_blur.cpp build/libgaussian_blur_%.so
	$(CXX) $(BASE) -O2 -Isrc $< -Lbuild -lgaussian_blur_$* -Wl,-rpath,'$(CURDIR)/build' -o $@

test: all $(addprefix build/test_,$(VARIANTS))
	@set -e; for variant in $(VARIANTS); do echo "Testing $$variant"; ./build/test_$$variant; done
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

clean:
	rm -rf build

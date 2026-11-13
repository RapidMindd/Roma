import argparse
import csv
import ctypes
import json
import os
from pathlib import Path
import platform
import time

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
VARIANTS = ('scalar_o0', 'scalar_o3', 'simd_o0', 'simd_o3', 'aligned_o0', 'aligned_o3')


class GaussianBlur:
    def __init__(self, variant="aligned_o3"):
        if variant not in VARIANTS:
            raise ValueError("Unknown variant")
        self.library = ctypes.CDLL(str(ROOT / "build" / f"libgaussian_blur_{variant}.so"))
        self.function = self.library.gaussian_blur
        pointer = ctypes.POINTER(ctypes.c_float)
        self.function.argtypes = [pointer, pointer] + [ctypes.c_int] * 4
        self.function.restype = ctypes.c_int

    def apply(self, image, iterations=1, threads=1):
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("Expected an RGB image with shape (height, width, 3)")
        height, width, _ = image.shape
        if not 0 < width <= 2**31 - 1 or not 0 < height <= 2**31 - 1:
            raise ValueError("Invalid image size")
        if not 0 <= iterations <= 2**31 - 1 or not 0 < threads <= 2**31 - 1:
            raise ValueError("Invalid iterations or threads")
        source = np.ascontiguousarray(image, dtype=np.float32)
        result = np.empty_like(source)
        pointer = ctypes.POINTER(ctypes.c_float)
        start = time.perf_counter()
        status = self.function(source.ctypes.data_as(pointer), result.ctypes.data_as(pointer),
                               width, height, iterations, threads)
        elapsed = time.perf_counter() - start
        if status:
            raise RuntimeError(f"Gaussian Blur failed with status {status}")
        return result, elapsed


def positive(value):
    number = int(value)
    if not 0 < number <= 2**31 - 1:
        raise argparse.ArgumentTypeError("Expected a positive 32-bit integer")
    return number


def load_image(path):
    with Image.open(path) as image:
        return np.array(image.convert("RGB"), dtype=np.float32)


def benchmark(args):
    if args.input:
        image = load_image(args.input)
    else:
        image = np.random.default_rng(42).integers(
            0, 256, (args.height, args.width, 3), dtype=np.uint8).astype(np.float32)
    complexity = sum(bool(line.strip()) for line in
                     (ROOT / "src" / "gaussian_blur.cpp").read_text().splitlines())
    records = []
    reference = None
    for variant in VARIANTS:
        blur = GaussianBlur(variant)
        threads = args.threads if variant == "parallel" else 1
        blur.apply(image, 1, threads)
        times = []
        for _ in range(args.repeats):
            result, elapsed = blur.apply(image, args.iterations, threads)
            times.append(elapsed)
            if reference is None:
                reference = result.copy()
            if not np.allclose(result, reference, rtol=0, atol=0.0001):
                raise RuntimeError(f"Results differ: {variant}")
        elapsed = float(np.median(times))
        record = dict(variant=variant, seconds=elapsed, performance=1 / elapsed,
                      complexity=complexity, efficiency=int(1e6 / elapsed / complexity),
                      speedup=records[0]["seconds"] / elapsed if records else 1.0,
                      threads=threads)
        records.append(record)
        print(f"{variant:12} T={elapsed:.6f} s  Perf={1 / elapsed:.6f}  "
              f"Comp={complexity}  P={record['efficiency']}  "
              f"speedup={record['speedup']:.2f}", flush=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    metadata = dict(platform=platform.platform(), machine=platform.machine(),
                    python=platform.python_version(), numpy=np.__version__,
                    width=image.shape[1], height=image.shape[0], iterations=args.iterations,
                    repeats=args.repeats, seed=42 if not args.input else None,
                    input=str(args.input) if args.input else None,
                    samples="median", timing="C ABI call including internal allocation and copies")
    args.csv.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Gaussian Blur: C++ and Python")
    commands = parser.add_subparsers(dest="command", required=True)
    blur = commands.add_parser("blur", help="Blur an RGB image")
    blur.add_argument("input", type=Path)
    blur.add_argument("output", type=Path)
    blur.add_argument("--variant", choices=VARIANTS, default="aligned_o3")
    blur.add_argument("--iterations", type=positive, default=1)
    blur.add_argument("--threads", type=positive, default=min(4, os.cpu_count() or 1))
    bench = commands.add_parser("benchmark", help="Compare available implementations")
    bench.add_argument("--input", type=Path)
    bench.add_argument("--width", type=positive, default=1920)
    bench.add_argument("--height", type=positive, default=1080)
    bench.add_argument("--iterations", type=positive, default=1000)
    bench.add_argument("--threads", type=positive, default=min(4, os.cpu_count() or 1))
    bench.add_argument("--repeats", type=positive, default=1)
    bench.add_argument("--csv", type=Path, default=ROOT / "results" / "benchmark.csv")
    args = parser.parse_args()
    try:
        if args.command == "benchmark":
            benchmark(args)
        else:
            result, elapsed = GaussianBlur(args.variant).apply(
                load_image(args.input), args.iterations, args.threads)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8)).save(args.output)
            print(f"Saved {args.output}; T={elapsed:.6f} s")
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()

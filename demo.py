from pathlib import Path

import numpy as np
from PIL import Image

from main import GaussianBlur


def main():
    directory = Path(__file__).resolve().parent / "results"
    directory.mkdir(exist_ok=True)
    y, x = np.indices((360, 640))
    pattern = ((x // 24 + y // 24) % 2) * 200 + 25
    image = np.stack((pattern, x * 255 // 639, y * 255 // 359), axis=-1).astype(np.uint8)
    Image.fromarray(image).save(directory / "demo_input.png")
    result, elapsed = GaussianBlur().apply(image, iterations=20, threads=4)
    Image.fromarray(np.rint(result).astype(np.uint8)).save(directory / "demo_blurred.png")
    print(f"Готово за {elapsed:.4f} с. Изображения: {directory}")


if __name__ == "__main__":
    main()

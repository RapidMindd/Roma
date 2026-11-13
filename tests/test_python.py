import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from main import GaussianBlur, ROOT, VARIANTS


class BindingTests(unittest.TestCase):
    def test_constant_and_noncontiguous_input(self):
        image = np.full((9, 17, 3), [10, 80, 200], dtype=np.float32)[:, ::2]
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                result, _ = GaussianBlur(variant).apply(image, 4, 2)
                np.testing.assert_array_equal(result, image)

    def test_invalid_input(self):
        blur = GaussianBlur()
        for image in (np.zeros((2, 3)), np.zeros((2, 3, 4)), np.zeros((0, 2, 3))):
            with self.assertRaises(ValueError):
                blur.apply(image)

    def test_image_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.png"
            target = Path(directory) / "output.png"
            image = np.random.default_rng(4).integers(0, 256, (13, 17, 3), dtype=np.uint8)
            Image.fromarray(image).save(source)
            subprocess.run([sys.executable, str(ROOT / "main.py"), "blur", str(source),
                            str(target), "--iterations", "2"], check=True, capture_output=True)
            expected, _ = GaussianBlur("scalar_o0").apply(image, 2)
            with Image.open(target) as output:
                np.testing.assert_array_equal(np.array(output), np.rint(expected).astype(np.uint8))

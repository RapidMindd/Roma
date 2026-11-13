#include "gaussian_blur.h"

#include <algorithm>
#include <cmath>
#include <iostream>
#include <random>
#include <vector>

static std::vector<float> reference(std::vector<float> src, int w, int h, int iterations)
{
    std::vector<float> dst(src.size());
    const int weights[] = {1, 2, 1};
    for (int n = 0; n < iterations; ++n) {
        for (int y = 0; y < h; ++y) {
            for (int x = 0; x < w; ++x) {
                for (int c = 0; c < 3; ++c) {
                    double sum = 0;
                    for (int dy = -1; dy <= 1; ++dy) {
                        for (int dx = -1; dx <= 1; ++dx) {
                            int iy = std::clamp(y + dy, 0, h - 1);
                            int ix = std::clamp(x + dx, 0, w - 1);
                            sum += src[(iy * w + ix) * 3 + c] * weights[dy + 1] * weights[dx + 1];
                        }
                    }
                    dst[(y * w + x) * 3 + c] = sum / 16;
                }
            }
        }
        src.swap(dst);
    }
    return src;
}

int main()
{
    std::mt19937 random(42);
    for (int h : {1, 2, 3, 7, 16}) {
        for (int w = 1; w <= 35; ++w) {
            std::vector<float> input(w * h * 3), output(input.size());
            for (float &value : input) {
                value = random() % 256;
            }
            for (int n : {0, 1, 4}) {
                auto expected = reference(input, w, h, n);
                for (int threads : {1, 3}) {
                    if (gaussian_blur(input.data(), output.data(), w, h, n, threads) != 0) {
                        return 1;
                    }
                    for (std::size_t i = 0; i < output.size(); ++i) {
                        if (std::abs(output[i] - expected[i]) > 0.0001f) {
                            std::cerr << "Mismatch: " << w << 'x' << h << " iteration " << n << '\n';
                            return 1;
                        }
                    }
                }
                auto inplace = input;
                if (gaussian_blur(inplace.data(), inplace.data(), w, h, n, 1) != 0 || inplace != output) {
                    return 1;
                }
            }
        }
    }
    float pixel[3] = {1, 2, 3};
    if (gaussian_blur(nullptr, pixel, 1, 1, 1, 1) != 1 ||
        gaussian_blur(pixel, pixel, 0, 1, 1, 1) != 1 ||
        gaussian_blur(pixel, pixel, 1, 1, -1, 1) != 1 ||
        gaussian_blur(pixel, pixel, 1, 1, 1, 0) != 1) {
        return 1;
    }
    std::cout << "OK: reference convolution, edges, SIMD tails, iterations, in-place, invalid arguments\n";
}

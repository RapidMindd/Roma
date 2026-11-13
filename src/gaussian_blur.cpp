#include "gaussian_blur.h"

#include <algorithm>
#include <cstdlib>
#include <limits>
#include <memory>


static void filter_row(const float *a, const float *b, const float *c,
                       float *out, std::size_t begin, std::size_t end)
{
    std::size_t i = begin;
    for (; i < end; ++i) {
        out[i] = (a[i] + 2.0f * b[i] + c[i]) * 0.25f;
    }
}

extern "C" int gaussian_blur(const float *input, float *output, int width,
                              int height, int iterations, int threads)
{
    if (!input || !output || width <= 0 || height <= 0 || iterations < 0 || threads <= 0) {
        return 1;
    }
    const std::size_t limit = std::numeric_limits<std::size_t>::max() / sizeof(float);
    if (static_cast<std::size_t>(width) > (limit - 16) / 3) {
        return 1;
    }
    const std::size_t row = static_cast<std::size_t>(width) * 3;
    const std::size_t stride = row;
    if (static_cast<std::size_t>(height) > (limit - 16) / stride) {
        return 1;
    }
    const std::size_t count = stride * height + 16;
    using Buffer = std::unique_ptr<float, decltype(&std::free)>;
    auto allocate = [count]() {
        void *p = std::malloc(count * sizeof(float));
        return Buffer(static_cast<float *>(p), &std::free);
    };
    Buffer first = allocate(), second = allocate(), temporary = allocate();
    if (!first || !second || !temporary) {
        return 2;
    }
    const int offset = 0;
    float *src = first.get() + offset;
    float *dst = second.get() + offset;
    float *tmp = temporary.get() + offset;
    for (int y = 0; y < height; ++y) {
        std::copy_n(input + y * row, row, src + y * stride);
    }
    for (int iteration = 0; iteration < iterations; ++iteration) {
        for (int y = 0; y < height; ++y) {
            const float *s = src + y * stride;
            float *t = tmp + y * stride;
            const std::size_t edge = std::min<std::size_t>(4, row);
            for (std::size_t i = 0; i < edge; ++i) {
                t[i] = (s[i < 3 ? i : i - 3] + 2.0f * s[i] + s[i + 3 < row ? i + 3 : i]) * 0.25f;
            }
            if (row > 7) {
                filter_row(s + 1, s + 4, s + 7, t + 4, 0, row - 7);
            }
            for (std::size_t i = std::max(edge, row > 3 ? row - 3 : 0); i < row; ++i) {
                t[i] = (s[i - 3] + 2.0f * s[i] + s[i]) * 0.25f;
            }
        }
        for (int y = 0; y < height; ++y) {
            filter_row(tmp + std::max(y - 1, 0) * stride, tmp + y * stride,
                       tmp + std::min(y + 1, height - 1) * stride,
                       dst + y * stride, 0, row);
        }
        std::swap(src, dst);
    }
    for (int y = 0; y < height; ++y) {
        std::copy_n(src + y * stride, row, output + y * row);
    }
    return 0;
}

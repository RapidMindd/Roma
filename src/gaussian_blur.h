#pragma once

#ifdef __cplusplus
extern "C" {
#endif

int gaussian_blur(const float *input, float *output, int width, int height,
                  int iterations, int threads);

#ifdef __cplusplus
}
#endif

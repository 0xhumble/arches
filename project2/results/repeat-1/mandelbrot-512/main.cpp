#include "stdafx.hpp"
#include "include.hpp"
#include "custom-instr.hpp"

// Pure per-pixel computation: no scene data, heap, or persistent mutable state.
inline uint32_t mandelbrot_pixel(uint x, uint y, uint width, uint height)
{
    constexpr uint max_iterations = 96;
    // Pixel centers; equal scale on both axes, including non-square images.
    const float scale = 3.2f / float(width);
    const float cr = -0.65f + (float(x) + 0.5f - 0.5f * float(width)) * scale;
    const float ci = (float(y) + 0.5f - 0.5f * float(height)) * scale;

    // These variables must be reset for EVERY work ID, not just at launch.
    float zr = 0.0f;
    float zi = 0.0f;
    uint iteration = 0;
    while (iteration < max_iterations && zr * zr + zi * zi <= 4.0f)
    {
        const float next_zr = zr * zr - zi * zi + cr;
        zi = 2.0f * zr * zi + ci;
        zr = next_zr;
        ++iteration;
    }

    // Finite-iteration interior estimate, not a proof of set membership.
    if (iteration == max_iterations)
        return 0xff'00'00'00;

    // Repeating polynomial palette: no pow/log/trigonometry or lookup table.
    const float t = float(iteration % 32u) / 32.0f;
    const float u = 1.0f - t;
    const uint red = uint(255.0f * (9.0f * u * t * t * t));
    const uint green = uint(255.0f * (15.0f * u * u * t * t));
    const uint blue = uint(255.0f * (8.5f * u * u * u * t));
    // Integer 0xAABBGGRR corresponds to RGBA bytes in little-endian memory.
    return 0xff'00'00'00 | red | (green << 8) | (blue << 16);
}

int main(void)
{
    const TRaXKernelArgs args = *(const TRaXKernelArgs*)TRAX_KERNEL_ARGS_ADDRESS;
    for (uint tid = fchthrd(); tid < args.framebuffer_size; tid = fchthrd())
    {
        const uint x = tid % args.framebuffer_width;
        const uint y = tid / args.framebuffer_width;
        args.framebuffer[tid] = mandelbrot_pixel(x, y, args.framebuffer_width,
                                               args.framebuffer_height);
    }
    return 0;
}

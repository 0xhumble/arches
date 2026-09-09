// Host-only validator: compile the exact submitted per-pixel arithmetic natively.
#define main trax_kernel_entry_not_called
#include "../src/trax-kernel/main.cpp"
#undef main
#include <cstdio>
#include <cstdlib>

int main(int argc, char** argv)
{
    if (argc != 3) return 2;
    const uint width = uint(std::strtoul(argv[1], nullptr, 10));
    const uint height = uint(std::strtoul(argv[2], nullptr, 10));
    if (width == 0 || height == 0) return 2;
    // Arches flips the framebuffer vertically before saving its PNG.
    for (uint row = 0; row < height; ++row)
        for (uint x = 0; x < width; ++x)
        {
            const uint32_t pixel = mandelbrot_pixel(x, height - 1 - row, width, height);
            const unsigned char rgba[] = {
                (unsigned char)pixel, (unsigned char)(pixel >> 8),
                (unsigned char)(pixel >> 16), (unsigned char)(pixel >> 24)};
            if (std::fwrite(rgba, 1, 4, stdout) != 4) return 1;
        }
    return 0;
}

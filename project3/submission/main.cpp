#include "stdafx.hpp"
#include "include.hpp"
#include "custom-instr.hpp"
#include "intersect.hpp"

int main(void)
{
    constexpr uint TILE_WIDTH = 4;
    constexpr uint TILE_HEIGHT = 8;
    constexpr uint TILE_SIZE = TILE_WIDTH * TILE_HEIGHT;
    static_assert(TILE_SIZE == 32);

    const TRaXKernelArgs args = *(const TRaXKernelArgs*)TRAX_KERNEL_ARGS_ADDRESS;
    const uint tiles_x = (args.framebuffer_width + TILE_WIDTH - 1) / TILE_WIDTH;
    const uint tiles_y = (args.framebuffer_height + TILE_HEIGHT - 1) / TILE_HEIGHT;
    const uint work_size = tiles_x * tiles_y * TILE_SIZE;
    for (uint tid = fchthrd(); tid < work_size; tid = fchthrd())
    {
        const uint tile_id = tid / TILE_SIZE;
        const uint offset = tid % TILE_SIZE;
        const uint x = (tile_id % tiles_x) * TILE_WIDTH + offset % TILE_WIDTH;
        const uint y = (tile_id / tiles_x) * TILE_HEIGHT + offset / TILE_WIDTH;
        if (x >= args.framebuffer_width || y >= args.framebuffer_height)
        {
            continue;
        }

        const rtm::Ray ray = args.camera.generate_ray_through_pixel(x, y);
        rtm::Hit hit;
        hit.t = ray.t_max;
        hit.bc = rtm::vec2(0.0f);
        hit.id = ~0U;
        _traceray<0x0U>(0, ray, hit);

        args.framebuffer[y * args.framebuffer_width + x] =
            hit.t < ray.t_max ? 0xff'00'00'ff : 0xff'4b'4b'4b;
    }
    return 0;
}

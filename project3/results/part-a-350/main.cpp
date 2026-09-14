// Project 3, page 5: deliberately preserve the original boundary bug.
#include "stdafx.hpp"
#include "include.hpp"
#include "custom-instr.hpp"

int main(void)
{
    const uint TILE_WIDTH = 4;
    const uint TILE_HEIGHT = 8;
    const uint TILE_SIZE = TILE_WIDTH * TILE_HEIGHT;
    static_assert(TILE_SIZE == 32);
    const TRaXKernelArgs args = *(TRaXKernelArgs*)TRAX_KERNEL_ARGS_ADDRESS;
    for (uint tid = fchthrd(); tid < args.framebuffer_size; tid = fchthrd())
    {
        uint tile_id = tid / TILE_SIZE;
        uint toffset = tid % TILE_SIZE;
        uint tile_x = tile_id % (args.framebuffer_width / TILE_WIDTH);
        uint tile_y = tile_id / (args.framebuffer_width / TILE_WIDTH);
        uint x = tile_x * TILE_WIDTH + toffset % TILE_WIDTH;
        uint y = tile_y * TILE_HEIGHT + toffset / TILE_WIDTH;
        uint fb_index = y * args.framebuffer_width + x;
        uint color = (tile_x & 0x1) ^ !(tile_y & 0x1)
                     ? 0xff'00'00'ff : 0xff'00'ff'00;
        args.framebuffer[fb_index] = color;
    }
    return 0;
}

#include "stdafx.hpp"
#include "include.hpp"
#include "custom-instr.hpp"

int main(void)
{
    const TRaXKernelArgs args = *(TRaXKernelArgs *)(TRAX_KERNEL_ARGS_ADDRESS);
#ifdef GRADIENT_SINGLE_PASS
    const uint tid = fchthrd();
    if (tid < args.framebuffer_size)
#else
    for (uint tid = fchthrd(); tid < args.framebuffer_size; tid = fchthrd())
#endif
    {
        uint x = tid % args.framebuffer_width;
        uint y = tid / args.framebuffer_width;
        uint red = 0xff * (float(x) / float(args.framebuffer_width));
        uint green = 0xff * (float(y) / float(args.framebuffer_height));
        uint color = 0xff'00'00'00;
        color |= red | (green << 8);
        args.framebuffer[tid] = color;
    }
    return 0;
}

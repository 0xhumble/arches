// Compile this translation unit with the simulator's native FP contraction
// settings (default -ffp-contract=fast), unlike the RISC-V shader/reference.cpp.
#include "stdafx.hpp"
#include "include.hpp"
#include "intersect.hpp"

void trace_reference(const rtm::CWBVH& bvh, const rtm::Ray& ray, rtm::Hit& hit)
{
    IntersectStats stats;
    intersect(bvh.nodes.data(), bvh.ftbs.data(), ray, hit, stats);
}

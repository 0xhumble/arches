// Functional oracle: CPU software traversal of the same compressed scene,
// without simulated hardware, caches, scheduling or memory interconnects.
#include "stdafx.hpp"
#include "include.hpp"

void trace_reference(const rtm::CWBVH& bvh, const rtm::Ray& ray, rtm::Hit& hit);

// RNG::randv2() constructs vec2(randf(), randf()). C++ does not specify
// argument evaluation order; the RISC-V kernel and host GCC may differ.
// Spell out the RISC-V binary's x-then-y order in the CPU oracle only.
static rtm::vec3 sample_hemisphere(const rtm::vec3& normal, rtm::RNG& rng)
{
    rtm::vec2 disk;
    do
    {
        float x = rng.randf();
        float y = rng.randf();
        disk = rtm::vec2(x, y) * 2.0f - rtm::vec2(1.0f);
    } while(rtm::length2(disk) > 1.0f);
    const rtm::vec3 sample(disk.x, disk.y, rtm::sqrt(1.0f - rtm::length2(disk)));
    const rtm::vec3 tan = rtm::calculate_arbitrary_tangent(normal);
    const rtm::vec3 bitan = rtm::cross(normal, tan);
    return rtm::normalize(sample[0] * tan + sample[1] * bitan + sample[2] * normal);
}

int main(int argc, char** argv)
{
    if(argc != 5) return 2; // dataset directory, size, output RGBA, metrics
    const std::string dir = argv[1];
    const uint size = std::stoul(argv[2]);
    rtm::Mesh mesh(dir + "/sponza.obj");
    if(mesh.vertex_indices.empty() || mesh.normals.empty()) return 3;
    for(const auto& indices : mesh.normal_indices)
        for(uint i = 0; i < 3; ++i)
            if(indices[i] >= mesh.normals.size()) return 4;
    rtm::CWBVH bvh(mesh, (dir + "/cache/sponza.bvh").c_str(), 0, false);
    const rtm::Camera camera(size, size, 12.0f, rtm::vec3(0, 2, 0), rtm::vec3(90, 0, -1));
    std::vector<uint32_t> pixels(size * size);
    uint64_t rays = 0, escaped = 0;
    for(uint y = 0; y < size; ++y)
        for(uint x = 0; x < size; ++x)
        {
            const uint index = y * size + x;
            rtm::RNG rng(index);
            rtm::Ray ray = camera.generate_ray_through_pixel(x, y);
            float throughput = 1.0f, radiance = 0.0f;
            for(uint bounce = 0; bounce < 3; ++bounce)
            {
                rtm::Hit hit(ray.t_max, rtm::vec2(0), ~0u);
                ++rays;
                trace_reference(bvh, ray, hit);
                if(hit.t >= ray.t_max)
                {
                    ++escaped;
                    radiance += throughput * 2.0f;
                    break;
                }
                const rtm::uvec3 ni = mesh.normal_indices.at(hit.id);
                const rtm::vec3 n = mesh.normals[ni[0]] * hit.bc.x
                    + mesh.normals[ni[1]] * hit.bc.y
                    + mesh.normals[ni[2]] * (1.0f - hit.bc.x - hit.bc.y);
                ray.o += ray.d * hit.t;
                ray.d = sample_hemisphere(n, rng);
                throughput *= 0.8f;
            }
            const uint32_t c = static_cast<uint32_t>(rtm::clamp(radiance, 0.0f, 1.0f) * 255.0f + 0.5f);
            pixels[index] = c | (c << 8) | (c << 16) | 0xff000000u;
        }
    std::ofstream out(argv[3], std::ios::binary);
    out.write(reinterpret_cast<const char*>(pixels.data()), pixels.size() * sizeof(uint32_t));
    std::ofstream metrics(argv[4]);
    metrics << "{\"rays\":" << rays << ",\"escaped_paths\":" << escaped
            << ",\"triangles\":" << mesh.vertex_indices.size()
            << ",\"bvh_node_bytes\":" << bvh.nodes.size() * sizeof(rtm::CWBVH::Node)
            << ",\"primitive_block_bytes\":" << bvh.ftbs.size() * sizeof(rtm::FTB)
            << ",\"normal_index_bytes\":" << mesh.normal_indices.size() * sizeof(rtm::uvec3)
            << ",\"normal_bytes\":" << mesh.normals.size() * sizeof(rtm::vec3) << "}\n";
    return out && metrics ? 0 : 5;
}

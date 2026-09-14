// CPU oracle: brute-force original OBJ triangles, without simulator/BVH traversal.
#include "stdafx.hpp"

int main(int argc, char** argv)
{
    if (argc != 5) return 2; // OBJ, width, height, output mask
    std::ifstream obj(argv[1]);
    if (!obj) return 3;
    std::vector<rtm::vec3> vertices;
    std::vector<rtm::Triangle> triangles;
    std::string line;
    while (std::getline(obj, line))
    {
        std::istringstream in(line);
        std::string kind;
        in >> kind;
        if (kind == "v")
        {
            rtm::vec3 v;
            in >> v.x >> v.y >> v.z;
            vertices.push_back(v);
        }
        else if (kind == "f")
        {
            std::vector<size_t> indices;
            std::string token;
            while (in >> token)
            {
                if (token[0] == '#') break;
                const int index = std::stoi(token.substr(0, token.find('/')));
                indices.push_back(index > 0 ? index - 1 : vertices.size() + index);
            }
            for (size_t i = 1; i + 1 < indices.size(); ++i)
            {
                rtm::Triangle tri;
                tri.vrts[0] = vertices.at(indices[0]);
                tri.vrts[1] = vertices.at(indices[i]);
                tri.vrts[2] = vertices.at(indices[i + 1]);
                triangles.push_back(tri);
            }
        }
    }
    if (triangles.empty()) return 4;
    const uint width = std::stoul(argv[2]), height = std::stoul(argv[3]);
    // Course scene presets: triangle and teapot share these camera parameters.
    const rtm::Camera camera(width, height, 24.0f, rtm::vec3(0, 0, 5), rtm::vec3(0));
    std::vector<uint8_t> mask(width * height);
    for (uint y = 0; y < height; ++y)
        for (uint x = 0; x < width; ++x)
        {
            const rtm::Ray ray = camera.generate_ray_through_pixel(x, y);
            rtm::Hit hit(ray.t_max, rtm::vec2(0), ~0U);
            for (const auto& tri : triangles) rtm::intersect(tri, ray, hit);
            mask[y * width + x] = hit.t < ray.t_max;
        }
    std::ofstream out(argv[4], std::ios::binary);
    out.write(reinterpret_cast<const char*>(mask.data()), mask.size());
    return out ? 0 : 5;
}

# Project 4 — measured results

Sponza, 512×512, 1 sample/pixel, up to 3 ray segments, 1.515 GHz, cold caches.

| Case | Cycles | Frame (ms) | Speedup vs C | DRAM reads (MiB) | L2 hit % | L3 hit % |
|---|---:|---:|---:|---:|---:|---:|
| a-8tm | 2,486,319 | 1.641135 | 0.9260× | 62.755 | 80.91 | - |
| b-64tm | 521,272 | 0.344074 | 4.4169× | 64.415 | 80.28 | - |
| c-l3-4m | 2,302,386 | 1.519727 | 1.0000× | 65.139 | 39.47 | 67.62 |
| l3-8m | 2,230,102 | 1.472015 | 1.0324× | 32.463 | 39.42 | 83.87 |
| l3-16m | 2,193,053 | 1.447560 | 1.0499× | 17.155 | 39.39 | 91.48 |
| l3-16m-lat528 | 2,414,834 | 1.593950 | 0.9534× | 17.150 | 39.43 | 91.48 |
| l3-16m-lat576 | 2,604,158 | 1.718916 | 0.8841× | 17.153 | 39.42 | 91.48 |

All configurations produce identical opaque pixels and the same total traced rays as the CPU reference. CPU reference differing pixels: 3/262144 (not claimed bit-exact unless zero).

Hit percentages exclude uncached stores; half-misses are requests merged into an outstanding miss, not ordinary cache hits.
The CPU reference shares scene/geometry code; it is an independent execution path, not an independently implemented geometry library.
Cache power parameters are uncalibrated; no energy/area/physical 3D-stacking conclusions are drawn.

# L2 MSHR sweep — measured results

Sponza 512×512; 64 TMs; eight local L2s; fixed 16 MiB L3, 480-cycle latency.

| MSHRs/local L2 | Cycles | Frame ms | Speedup vs 192 | L2 hit % | L2 MSHR stalls | DRAM read MiB |
|---|---:|---:|---:|---:|---:|---:|
| 192 | 2,193,053 | 1.447560 | 1.0000× | 39.389 | 54,071,109 | 17.155 |
| 384 | 1,140,945 | 0.753099 | 1.9221× | 39.165 | 21,549,666 | 17.150 |
| 768 | 951,937 | 0.628341 | 2.3038× | 38.704 | 14,723,759 | 17.154 |

Best measured case: **l2-mshr768**.

192 reproduces every recorded performance counter from the previous capacity study.
All images match the previous study exactly; the known three CPU-reference pixel differences remain.
MSHR Stalls includes return/miss-queue backpressure and is not a direct MSHR-occupancy metric.
Repeat checks: {"l2-mshr768": {"all_recorded_metrics_identical": true, "pixels_identical": true, "cycles": 951937}}

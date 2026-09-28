#set page(paper: "us-letter", margin: (x: 0.65in, y: 0.5in))
#set text(font: "Libertinus Serif", size: 10.5pt)
#set par(leading: 0.45em)
#set heading(numbering: none)
#set block(spacing: 0.65em)

#align(center)[
  #text(size: 17pt, weight: "bold")[CS 6959 — Project 4]
  #linebreak()
  Modifying Hardware Configuration
]

All configurations use the same kernel and Sponza scene at 512 × 512, 1 sample per pixel, up to three ray segments, and a 1.515 GHz simulated clock.

#table(
  columns: (1fr, auto, auto),
  inset: 5pt,
  align: (left, right, right),
  [*Configuration*], [*Cycles*], [*Frame time (ms)*],
  [A: 8 TMs, two-level cache], [2,486,319], [1.641135],
  [B: 64 TMs, two-level cache], [521,272], [0.344074],
  [C: 64 TMs, three-level cache], [2,302,386], [1.519727],
  [Optimized C: 384 MSHRs per L2], [1,223,485], [0.807581],
)

== a. Increasing TMs from 8 to 64
B is *4.77× faster* than A. Scaling is less than 8× because more TMs do not proportionally increase shared memory-system resources or eliminate memory stalls.

== b. Adding a third cache level
C takes *4.42× as long* as B. Its group-local L2 caches have a lower hit rate, so many requests must traverse the additional 480-cycle L3 stage. The added hierarchy therefore hurts performance on this workload.

== c. L2 hit and miss rates
#table(
  columns: (1fr, auto, auto, auto),
  inset: 5pt,
  align: (left, right, right, right),
  [*L2 organization*], [*Hit*], [*Half miss*], [*Miss*],
  [B: shared across all 64 TMs], [80.28%], [0.41%], [19.31%],
  [C: one L2 per 8 TMs], [39.47%], [0.36%], [60.17%],
)
Half misses merge into an outstanding miss; they are not ordinary hits. Both designs have 4 MiB of L2 in total, but each group in C can use only its own 512 KiB. Restricted sharing and duplicated data across groups help explain the lower hit rate.

== d. Selected optimization
Increase only the new L2’s #raw("num_mshr") from *192 to 384*. Keep C’s topology, 4 MiB L3, 480-cycle L3 latency, and all other hardware parameters unchanged. More MSHRs allow more cache misses to remain in flight, reducing backpressure while data returns.

The change gives *1.88× speedup over C*, reducing frame time by *46.86%*. L2’s reported MSHR/queue-stall count falls from 57,419,578 to 23,603,232, while DRAM reads remain approximately 68.3 MB. This supports increased miss concurrency, rather than reduced memory traffic, as the source of improvement.

#align(center)[
  #image("selected/results/c-mshr384/out.png", width: 2.0in)
  #linebreak()
  #text(size: 9pt)[Sponza, 512 × 512. All four configurations produce identical images.]
]

#set page(paper: "us-letter", margin: (x: 0.7in, y: 0.55in))
#set text(font: "Libertinus Serif", size: 11pt)
#set par(leading: 0.6em)
#set heading(numbering: none)
#align(center)[
  #text(size: 18pt, weight: "bold")[CS 6959 — Project 3]
  #linebreak()
  #text(size: 13pt)[Ray Tracing Kernels]
]

== A. Pixel–tile mapping
#align(center)[
  #image("results/part-a-350/out.png", width: 2.85in)
  #linebreak()
  Page 5 kernel, unmodified mapping; 350 × 350 framebuffer.
]

== B. Primary ray visibility
#grid(columns: (1fr, 1fr), gutter: 0.25in,
  align(center)[
    #image("results/triangle-350/out.png", width: 2.85in)
    #linebreak()
    (a) `--scene-name=triangle` · 350 × 350
  ],
  align(center)[
    #image("results/teapot-350/out.png", width: 2.85in)
    #linebreak()
    (b) `--scene-name=teapot` · 350 × 350
  ],
)

Each 32-thread tile processes a 4 × 8 pixel region. Rounded-up tile counts and bounds checks handle partial edge tiles without mixing distant pixels. One camera ray is traced per valid pixel using `_traceray<0x0U>(0, ray, hit)`; hits are red and misses dark gray.

Simulator termination fixes prevent repeated halt counting and drain pending framebuffer stores. Both visibility images match a CPU brute-force triangle-intersection reference at every pixel. Submitted separately: `main.cpp` and one `trax_log.txt` containing both Part B runs.

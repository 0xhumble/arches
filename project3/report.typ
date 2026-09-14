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
  350 × 350
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

#set page(paper: "a4", margin: 20mm)
#set text(font: "Libertinus Serif", size: 11pt)
#set par(leading: 0.55em)

#align(center, text(size: 16pt, weight: "bold")[Project 2 — Authoring Kernels])

*1. How long did it take to simulate the color-gradient kernel?*

The 256 × 256 run took 0.865 s end-to-end on the host. The simulator reported 1 s for its simulation-loop timer, rounded to whole seconds.

*2. In what color format is color written to the framebuffer?*

32-bit `0xAABBGGRR`: red in bits 0–7, green in 8–15, blue in 16–23, and alpha in 24–31. The little-endian byte order is RGBA.

*3. What is an execution model? What constitutes TRaX's execution model?*

An execution model specifies how threads execute, are grouped, and interact. TRaX's model consists of threads and tiles: each thread executes on one TP, and each tile's threads execute within one TM. A default tile contains 32 consecutive work IDs.

*4. What purpose does `fchthrd()` serve?*

`fchthrd()` atomically obtains a unique work ID, allowing available execution contexts to claim more work through tile scheduling. Repeated calls let the kernel process more pixels than there are hardware contexts.

#v(4pt)
#grid(
  columns: (1fr, 1fr),
  gutter: 12pt,
  figure(image("results/gradient-256/out.png", width: 53mm), caption: [Color gradient, 256 × 256.]),
  figure(image("results/mandelbrot-512/out.png", width: 53mm), caption: [Mandelbrot submission, 512 × 512.]),
)

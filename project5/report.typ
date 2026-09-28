#set page(paper: "us-letter", margin: 0.7in)
#set text(font: "Libertinus Serif", size: 11pt)
#set par(leading: 0.6em)
#set heading(numbering: none)

#align(center)[
  #text(size: 18pt, weight: "bold")[CS 6959 — Project 5]
  #linebreak()
  Adding Custom Instructions
]

== a. U-encoding in TRaX versus RISC-V
RISC-V U-format has a 20-bit immediate, a 5-bit destination register, and a 7-bit opcode. Under the custom-0 opcode, TRaX splits that immediate into #raw("funct3 = bits[14:12]") and #raw("func_code = bits[31:15]"), with #raw("funct3 = 0") selecting its U-encoded instructions.

== b. Why is the immediate 0x00018?
BaryInterp3 uses #raw("func_code = 3") and #raw("funct3 = 0"), so #raw("imm = (3 << 3) | 0 = 0x00018"). With #raw("rd = x0") and opcode #raw("0x0b"), the complete instruction word is #raw("0x0001800b").

== c. Changes in kernel.dump
Without the custom instruction, interpolation uses ordinary floating-point arithmetic such as #raw("fmul.s"), #raw("fmadd.s"), #raw("fadd.s"), and #raw("fsub.s"). With it, the dump contains #raw("0001800b .insn 4, 0x0001800b") at two compiler-generated sites, with inputs placed in #raw("f0–f10") and results consumed from #raw("f28–f30").

#align(center)[
  #image("custom-fixed/out.png", width: 3.8in)
  #linebreak()
  Sponza, 512 × 512, rendered using BaryInterp3.
]

# Project 5 — Adding Custom Instructions

Base: upstream `146642691df5b1101a25ba5821dce6a67ece318f`, in a fresh worktree. No Project 3 fixes or Project 4 hardware changes are included.

Only the handout's three source files are changed: the kernel, the simulator instruction table/name registration, and the TRaX TP dependency check. Hardware and build flags remain upstream defaults.

- `software/`: completed Part B kernel and its disassembly, before using the instruction.
- `custom/`: custom-instruction kernel executable/disassembly, build logs, simulation log and image.
- `0001800b` appears at two compiler-generated sites in the custom dump and is absent from the software dump.

Simulation command (run from `project5/custom/`):

```sh
../../build/src/arches-v2/arches-v2 --arch-name=TRaX --dataset-dir=/root/datasets --scene-name=sponza --framebuffer-width=512 --framebuffer-height=512 --pregen-rays=0 --bvh-preset=0 --bvh-merging=0 --logging-interval=100000
```

**Pending user decision:** the simulator exits successfully and logs BARYINT3 execution, but the raw output has 17 transparent/unwritten pixels out of 262,144. This resembles the previously encountered upstream termination issue; no termination fix has been applied here. The report and final submission package are not yet prepared pending this decision.

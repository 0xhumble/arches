.PHONY: make riscv riscv-dissasm clean
make: riscv riscv-dissasm

# Explicit single-precision target; deterministic arithmetic for CPU validation.
riscv: main.cpp
	mkdir -p riscv
	riscv64-unknown-elf-g++ -march=rv64imaf -mno-relax -nostartfiles -emain -Wstack-usage=512 -mabi=lp64f -O3 -ffp-contract=off -I ../../include ./main.cpp -o ./riscv/kernel

riscv-dissasm: riscv
	riscv64-unknown-elf-objdump -d -x ./riscv/kernel > ./riscv/kernel.dump

clean:
	rm -f riscv/*
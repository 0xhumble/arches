# Project 3 — Ray Tracing Kernels

## 提交文件

`submission/` 中只有作业要求的三个文件：

- `main.cpp`：Part B kernel，与 `src/trax-kernel/main.cpp` 完全相同。
- `trax_log.txt`：triangle 和 teapot 两次 Part B 仿真的完整日志，直接拼接，没有额外说明或删改统计。
- `report.pdf`：一页报告，仅包含标题、Part A、triangle、teapot 三张最终原始仿真图及必要标注，不包含实现、验证或模拟器修复说明。

所有最终图片均为 350×350。Part A 严格保留讲义 Page 5 的原始映射；Part B 用向上取整的 tile 网格、填充工作 ID 和边界检查修复边缘像素遗漏。每个 32-ID block 仍只覆盖一个 4×8 区域；无效 ID 使用 `continue` 而非退出 worker。每个有效像素生成一条主射线，命中红色、未命中深灰色。不使用预生成射线、材质、纹理或二次射线。

## 复现

在仓库根目录运行。依赖：现有课程 RISC-V toolchain（`/opt/riscv/bin`）、CMake/G++、数据集 `/root/datasets`、uv。长命令请通过 tmux 运行。

```bash
cmake --build build --target arches-v2 -j 4
# 默认拒绝覆盖已有结果；重新实验请选择新的 --results 目录。
python3 project3/run.py --results /tmp/project3-results
uv run --with pillow python project3/validate.py
uv run --with typst python project3/package.py
```

`validate.py` 验证仓库 `project3/results/` 内的最终结果；`package.py` 同样使用该目录。`run.py --case part-a|triangle|teapot --size N` 可单独实验。编译与仿真必须串行，因为模拟器读取固定的 `src/trax-kernel/riscv/kernel`。每组结果保存源文件、ELF、反汇编、编译日志、仿真日志、PNG，以及命令、返回码和 SHA-256 元数据。

## 正确性验证

- 映射：穷举 1…33 的所有宽高组合，再测 255×256、256×256、257×256、350²、360²、512²，共 1,095 组尺寸；检查每个有效像素恰好处理一次。
- Part A：逐像素复现原始映射。350² 时右侧 700 个像素未写入，且原始 kernel 有 700 次越过 framebuffer 尾部的写入；这是讲义示例自身的边界错误，不把它带入 Part B。
- Part B：`reference.cpp` 直接读取原始 OBJ 顶点/面，在 CPU 上对所有三角形暴力求交，不经过模拟器或 BVH。相机及单精度求交函数使用课程 rtm 库。比较时撤销 Arches 保存 PNG 时的垂直翻转；要求颜色、透明度、命中与未命中全部逐像素一致。
- 检查结果见 `validation.json`。triangle 和 teapot 各重复三次（含最终运行），PNG 字节完全相同，摘要见 `regression.json`。没有对最终 PNG 修补、填色或后处理。

## 模拟器终止修复

原始模拟器在 350² teapot 中留下 53 个透明像素；512² 也有 25 个。只补写请求排空后，350² 仍遗漏 5 个像素。进一步定位出两个终止条件缺陷，本分支同时修复：

1. **posted stores 的存活计数**：普通 STORE 没有返回依赖，TP 退出后仍可能滞留于缓存、crossbar 或 DRAM 输入网络。`UnitCache` / `UnitCrossbar` 在接收 STORE 时增加 `units_executing`，交给下一层（下一层先增加计数）后再减少。DRAM 在接受写入并更新功能内存后减少。这保证 readback 之前所有已发出的写入都可见，不是添加固定延时，也不宣称等待 DRAM 电气时序完全结束。
2. **halt 重复计数**：`UnitTP::clock_fall()` 的无就绪线程 fallback 可能选中已经退出的 `_last_thread_id`，反复执行旧 RET、重复增加 `_num_halted_threads`，在其他线程仍等待射线结果时错误宣告整个 TP 结束。现在对 `pc == 0` 移出就绪队列并直接返回，且晚到的 SFU/load 返回不会重新入队已退出线程，退出只计数一次。

这些是模拟器正确性修复，不改变 tile scheduler、ISA、射线结果、缓存容量或延迟。修复说明仅保留在本 README，不放入提交报告；kernel 本身无忙等或模拟器特定延时。要严格重现最终日志，请使用本分支构建模拟器，而不是未修复版本。调试阶段的未修复图片不属于最终提交图。

日志中的 teapot 材质读取器 `Invalid line: 11` 是已有 MTL 解析提示，不影响仅用几何的 visibility kernel。`MRays/J: inf` 来自上游功耗函数返回零，不用于报告性能结论。

# Project 2 — TRaX Mandelbrot

## 仓库与环境

- 最新上游基线：`97bebdcd75948baf72d6334890d2793ccd66afe6`。
- 工作目录：`/root/arches`，分支 `project2/mandelbrot`。
- Project 1 原仓库整体保留在 `/root/arches-project1`，没有更改其内容或分支。其旧 CMake 缓存包含改名前的绝对路径，如需重建应使用新的 build 目录。
- `upstream` 是 Utah-Graphics-Lab/arches（只读取），`origin` 是自己的 0xhumble/arches（保存分支）。
- 课程提供的工具链安装在 `/opt/riscv`，GCC 15.2.0，单一 `rv64imfa/lp64f` 配置，无 multilib；PATH 已加入 `/root/.bashrc`。
- 模拟器：Release 构建，默认 RTX 2080-ish 配置，46 TM × 64 TP × 8 上下文，32 ID/tile，1515 MHz。**没有修改模拟器或硬件源码。**
- 主机：Debian 13 x86-64 LXC；12 个可用逻辑 CPU，模拟器上游代码把 TBB 最大并行度设为 8。

## 成果

- `../src/trax-kernel/main.cpp`：最终提交 kernel，512×512 彩色 Mandelbrot，96 次迭代上限。
- `report.pdf`：3 页英文报告，回答作业全部四个问题，含渐变、无循环对照、正式分形及异常试跑说明。
- `report.typ`：可编辑的报告源文件。
- `results/mandelbrot-512/`：正式原始图片、日志、源码快照、ELF、反汇编、编译日志、命令与 SHA-256 元数据。
- `results/gradient-256/` 与 `results/single-pass-256/`：讲义渐变和去掉循环的对照。
- `results/repeat-{1,2}/`：512×512 的两次独立重复运行，像素和周期数一致。
- `validation.json`：正式结果的逐像素验证，全部零差异。
- `exploratory/`：256×256 分形的失败试跑；保留原始证据，不计为测试通过。

提交包另外复制到 `/root/project2/submission/`：`main.cpp`、`trax_log.txt`、`out.png`、`report.pdf`。报告没有虚构姓名/学号，可按课程要求自行补充。

## 核心结果

| 实验 | 主机完整进程耗时（秒） | 模拟周期 | 模拟帧时间 | 验证 |
|---|---:|---:|---:|---|
| 渐变 256² | 0.865166 | 8,874 | 0.00586 ms | 65,536 像素全部正确 |
| 无循环 256² | 0.594484 | 5,089 | 0.00336 ms | 恰好 23,552 像素写入 |
| 分形 512² | 2.757983 | 33,755 | 0.0223 ms | 262,144 像素全部正确 |

主机计时通过 Python `time.perf_counter()` 包围模拟器子进程，不含编译，含初始化和 PNG 输出。日志 `Simulation time` 只测模拟循环且四舍五入到整数秒，因此渐变日志显示 1 s，正式分形显示 2 s。以上是原始单次测量，不是均值。

## 复现

```sh
export PATH=/opt/riscv/bin:$PATH
cd /root/arches
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --target arches-v2 -j 8
cd src/trax-kernel
make
```

Makefile 显式指定 `rv64imaf/lp64f`，使用 `-O3 -ffp-contract=off`（替代上游 `-Ofast`），便于与 CPU 使用相同浮点运算边界核对。PHONY 目标确保头文件变动后也实际重编译，并创建输出目录。`riscv/kernel` 是模拟器固定读取的文件。

运行单个正式实验：

```sh
mkdir -p /root/project2/reproduced
cd /root/project2/reproduced
/root/arches/build/src/arches-v2/arches-v2 \
  --arch-name=TRaX --dataset-dir=/root/datasets --scene-name=teapot \
  --framebuffer-width=512 --framebuffer-height=512 \
  --pregen-rays=0 --logging-interval=100000 > trax_log.txt 2>&1
```

完整流程通过 tmux 后台执行（不会覆盖已经存在的结果目录）：

```sh
tmux new-session -d -s project2-reproduce \
  'cd /root/arches && python3 project2/run.py --results project2/reruns > /root/project2/reproduce.log 2>&1'
```

`run.py` 默认按顺序运行渐变 256²、无循环 256²、分形 512²。可用 `--case`、`--size`、`--dataset-dir` 控制；一次只能运行一个 runner，因为所有实验都会替换模拟器固定加载的 `src/trax-kernel/riscv/kernel`。最后一次实验是分形，不会修改最终 `main.cpp`。

验证已保存的正式结果：

```sh
cd /root/arches
uv run --with pillow python project2/validate.py
```

验证包括：命令退出码、源码/ELF SHA-256、尺寸、渐变解析值、无循环未写区域、分形与同一 C++ 像素函数的 CPU 字节级对照。它验证模拟器执行结果，不是独立实现的数学 oracle；不会扫描 `exploratory/`。所有正式 512² 图片 SHA-256 均为：

```text
5d993eae9ddee9d54ee767868bc1b96379c92d237629f8647c3cb0831140d21b
```

额外做过的原生 sanitizer 检查（257×223 非方形）：

```sh
g++ -std=c++20 -O1 -ffp-contract=off -march=native \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I include project2/reference.cpp -o /tmp/project2-reference
/tmp/project2-reference 257 223 > /dev/null
```

重新生成 PDF：

```sh
uv run --with typst python -c \
  'import typst; typst.compile("project2/report.typ", output="project2/report.pdf", root="project2")'
```

## 已知问题与边界

1. **256² 分形异常**：2 个像素透明，L1 uncached requests = 65,536，DRAM stores = 65,534。推测是上游模拟器结束条件/写队列排空问题，尚未证明根因，也没有修改硬件源码或添加 kernel 延时绕过。失败原始文件及当时验证结果保留在 `exploratory/`。最终 512² 三次运行都逐字节通过，但不能由此推断任意尺寸均无此问题。
2. 主机仍加载场景和 BVH，即便图案 kernel 不用它们，所以选择小型 `teapot`。材质读取器打印 `Invalid line: 11`，不影响本 kernel 的输出。
3. 零射线工作负载的 RT Core 比率会有 `nan`；不要把 ray throughput/power 等字段当作本实验有效测量。
4. 分形黑色表示 96 次内未逃逸，不是严格数学上的集合归属。色带故意保留，没有抗锯齿或平滑着色。
5. 未向课程上游提交 issue/PR，也未将课程 PDF、工具链或 datasets 放进 Git。

# FlashAttention-2 Cluster Multi-Architecture Installation Manual

This manual documents the standardized deployment protocol for FlashAttention-2 (v2.8.4) across the heterogeneous L20 cluster using a unified container-image-aware strategy.

## Cluster Environment Overview

The cluster consists of heterogeneous nodes running as **OverlayFS containers**:
- **GPU Master Node (`gpu`)**: Sm89 (Ada Lovelace / L20) architecture.
- **ARM Cluster Nodes (`arm-32`, `arm-33`, `arm-34`)**: Sm89 (L20) optimized ARM nodes.

### Prerequisites

| Component | Shared/Local | Standard Version |
| :--- | :--- | :--- |
| **Python Environment** | Shared Container Root | Python 3.12.3 (Local) |
| **Compiler Paths** | Shared Container Root | GCC 11.4+, CUDA 12.4+ |
| **Build Staging** | Local Node SSD | `/tmp/fa2_build/` |
| **NAS Persistence** | Shared Mount | `/jhdx0003008/cache/wheels/` |

---

## 🚀 Unified Installation Strategy

### 1. Build & Install Once per Architecture
Due to the **shared container image** architecture (OverlayFS), installing FlashAttention-2 on *one* node of a specific architecture subset results in global availability across nodes sharing that image layer.

- **ARM Branch**: Perform the build on `arm-32`. Once verified, it is automatically available to `arm-33` and `arm-34`.
- **GPU Branch**: Perform the build on the `gpu` Master node.

### 2. Sm89 Performance Acceleration
Compilation of Sm89 kernels is high-latency. Follow these critical settings to bypass GPFS bottlenecks:

1. **Localize Source**: Copy source code to local SSD (`/tmp/`) before building.
2. **Gold Linker**: Force `LDFLAGS="-Wl,--fuse-ld=gold"` to accelerate the linking of large (>2GB) object files.
3. **Parallelism**: Use `MAX_JOBS=32` on GPU Master and `MAX_JOBS=16` on ARM.

---

## 🛠️ Step-by-Step Instructions

### For ARM Nodes (Sm89 / L20)

```bash
# 1. Enter the build staging directory
cd /tmp/arm_fa2_src

# 2. Configure environment
export FLASH_ATTN_CUDA_ARCHS=89
export MAX_JOBS=16

# 3. Build and Install
# Target local Python 3.12 
python3 setup.py bdist_wheel
pip install dist/flash_attn*.whl

# 4. Flush to NAS Cache (Optional for non-shared environments)
cp dist/*.whl /jhdx0003008/cache/wheels/
```

### For GPU Master (Sm89 / L20)

```bash
# 1. Localize to high-speed SSD
mkdir -p /tmp/gpu_fa2_localized
cp -rv /source/path/flash-attn /tmp/gpu_fa2_localized/

# 2. Configure Accelerated Linking
export FLASH_ATTN_CUDA_ARCHS=89
export MAX_JOBS=32
export LDFLAGS="-Wl,--threads=32 -Wl,--fuse-ld=gold"

# 3. Build & Global Install
cd /tmp/gpu_fa2_localized
python3 setup.py bdist_wheel
pip install dist/flash_attn*.whl
```

---

## ✅ Verification Protocol

Run the following command on *any* node within the same architecture group to verify propagation:

```python
python3 -c "import flash_attn; print(f'FA2 Version: {flash_attn.__version__}')"
```

---

## ⚠️ Troubleshooting

### Linker Stalls
If the `ld` process hangs during the final linking phase (likely on the GPU Master), ensure:
- You are building in `/tmp/` (Local SSD), **NOT** on `/jhdx` (GPFS).
- You are using `ld.gold` via LDFLAGS.

### Architecture Mismatch
If you see "No CUDA kernels found" error:
- Ensure `FLASH_ATTN_CUDA_ARCHS=89` was set during both compilation and installation.

---
name: "burn-cuda"
description: "Burn CUDA backend - High-performance NVIDIA GPU acceleration. Provides optimal performance for NVIDIA hardware."
---

# burn-cuda

## Overview

`burn-cuda` provides NVIDIA GPU acceleration using CUDA. It's optimized for NVIDIA GPUs and provides the best performance for NVIDIA hardware.

## Key Features

- **NVIDIA CUDA Support**: Direct access to CUDA cores
- **High Performance**: Optimized for NVIDIA GPUs
- **Tensor Cores**: Support for mixed-precision computing
- **CUDA Toolkit Integration**: Uses NVIDIA's CUDA toolkit

## Usage

### Basic Setup

```rust
use burn::tensor::Tensor;
use burn_cuda::CudaDevice;

// Create CUDA device
let device = CudaDevice::default();

// Create tensor on GPU
let tensor = Tensor::from_data(&[1.0, 2.0, 3.0], &device);

// CUDA-accelerated operations
let result = tensor.matmul(other_tensor);
```

### Backend Type

```rust
use burn_cuda::CudaBackend;

type Backend = CudaBackend;
let model: Model<Backend> = Model::default();
```

### burn.toml Configuration

```toml
[model_exports]
default_backend = "cuda"
default_device = "Gpu"

[cuda]
```

## Requirements

- NVIDIA GPU with CUDA support
- CUDA Toolkit installed
- Linux or Windows operating system

## Best Practices

1. Use for maximum GPU performance
2. Enable mixed-precision training
3. Monitor GPU memory usage
4. Use batch processing for optimal throughput

## Performance Considerations

- Best performance on NVIDIA GPUs
- Requires NVIDIA hardware
- Not available on macOS (use burn-metal instead)
- Excellent for large-scale training

## When to Use

- NVIDIA GPU deployment
- High-performance training
- Production inference on NVIDIA hardware
- Research with large models

## Related Crates

- `burn`: Core framework
- `burn-metal`: Apple GPU alternative for macOS/iOS
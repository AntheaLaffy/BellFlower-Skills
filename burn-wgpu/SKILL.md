---
name: "burn-wgpu"
description: "Burn WGPU backend - Cross-platform GPU acceleration using WebGPU. Supports Vulkan, Metal, Direct3D, and WebGL."
---

# burn-wgpu

## Overview

`burn-wgpu` provides cross-platform GPU acceleration using WebGPU through the `wgpu` crate. It supports:

- **Vulkan**: Linux, Android
- **Metal**: macOS, iOS
- **Direct3D 12**: Windows
- **WebGL**: Web browsers

## Key Features

- **Cross-platform GPU**: Works on all major platforms
- **Web Support**: Runs in browsers via WASM
- **Automatic Shader Generation**: No manual shader writing
- **Memory Efficient**: Smart memory management

## Usage

### Basic Setup

```rust
use burn::tensor::Tensor;
use burn_wgpu::WgpuDevice;

// Create GPU device
let device = WgpuDevice::default();

// Create tensor on GPU
let tensor = Tensor::from_data(&[1.0, 2.0, 3.0], &device);

// GPU-accelerated operations
let result = tensor.matmul(other_tensor);
```

### Backend Type

```rust
use burn_wgpu::WgpuBackend;

type Backend = WgpuBackend;
let model: Model<Backend> = Model::default();
```

### burn.toml Configuration

```toml
[model_exports]
default_backend = "wgpu"
default_device = "Gpu"

[wgpu]
```

## Best Practices

1. Use for production GPU inference
2. Enable `wgpu` feature for WebAssembly
3. Profile memory usage for large models
4. Use async operations for better performance

## Performance Considerations

- Significantly faster than CPU for large tensors
- Memory transfer overhead between CPU/GPU
- Best for batch processing and large models
- WebAssembly performance may vary by browser

## When to Use

- Production GPU inference
- Cross-platform applications
- Web-based ML applications
- High-performance training

## Related Crates

- `burn`: Core framework
- `burn-onnx`: ONNX model import with GPU acceleration
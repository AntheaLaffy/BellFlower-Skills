---
name: "burn-ndarray"
description: "Burn NdArray backend - CPU-based tensor operations using Rust's ndarray crate. Ideal for development, testing, and lightweight inference."
---

# burn-ndarray

## Overview

`burn-ndarray` provides a CPU backend for Burn using the Rust `ndarray` crate. It's the default backend for development and testing.

## Key Features

- **CPU Computing**: All tensor operations run on CPU
- **Easy Setup**: No GPU dependencies required
- **Cross-platform**: Works on Linux, Windows, macOS
- **WASM Support**: Can compile to WebAssembly

## Usage

### Basic Setup

```rust
use burn::tensor::Tensor;
use burn_ndarray::NdArrayDevice;

// Create device
let device = NdArrayDevice::default();

// Create tensor
let tensor = Tensor::from_data(&[1.0, 2.0, 3.0], &device);

// Perform operations
let result = tensor + 2.0;
```

### Backend Type

```rust
use burn_ndarray::NdArrayBackend;

type Backend = NdArrayBackend;
let model: Model<Backend> = Model::default();
```

### burn.toml Configuration

```toml
[model_exports]
default_backend = "ndarray"
default_device = "Cpu"

[ndarray]
```

## Best Practices

1. Use for development and testing
2. Good for small to medium models
3. Ideal for WASM deployments
4. Use with `burn-onnx` for CPU inference

## Performance Considerations

- Single-threaded by default
- Good for prototyping
- Not recommended for large-scale training
- Use `burn-wgpu` or `burn-cuda` for GPU acceleration

## When to Use

- Development and debugging
- CI/CD pipelines
- WASM applications
- Lightweight inference
- Embedded systems without GPU

## Related Crates

- `burn`: Core framework
- `burn-onnx`: ONNX model import for CPU inference
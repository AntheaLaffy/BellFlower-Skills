---
name: "burn"
description: "Provides guidance on using Burn deep learning framework for Rust projects. Invoke when working with tensor operations, model inference, or ONNX model integration in Rust."
---

# Burn Deep Learning Framework Guide

## Overview

Burn is a next-generation deep learning framework for Rust with primary goals:
- **Extreme flexibility**: Generic over Backend trait for swappable backends
- **Compute efficiency**: Zero-cost abstractions, automatic kernel fusion
- **Portability**: Run on CPU, GPU, and embedded devices

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Code Layer                         │
│     Model, Layer, Training Loop, Custom Operations          │
├─────────────────────────────────────────────────────────────┤
│                    High-level API Layer                     │
│     nn::Module, Optimizer, Loss, DataLoader, Scheduler     │
├─────────────────────────────────────────────────────────────┤
│                    Core Abstraction Layer                   │
│     Tensor<T, B>, Backend Trait, Autodiff                  │
├─────────────────────────────────────────────────────────────┤
│                    Backend Implementation Layer             │
│     burn-ndarray, burn-wgpu, burn-cuda, burn-metal         │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Core Crates

| Crate | Purpose |
|-------|---------|
| `burn` | Core framework with tensor operations and autodiff |
| `burn-ndarray` | CPU backend based on ndarray |
| `burn-wgpu` | Cross-platform GPU backend (WebGPU) |
| `burn-cuda` | NVIDIA CUDA backend |
| `burn-metal` | Apple Metal backend |
| `burn-onnx` | ONNX model import and code generation |

### 2. Tensor Basics

```rust
use burn::tensor::Tensor;
use burn_ndarray::NdArrayDevice;

let device = NdArrayDevice::default();

// Create tensor from data
let tensor = Tensor::from_data(&[1.0, 2.0, 3.0], &device);

// Tensor operations
let result = tensor + 2.0;
let matmul = tensor.matmul(other_tensor);
```

### 3. Backend Trait (Core Abstraction)

```rust
pub trait Backend: Clone + Send + Sync + 'static {
    type TensorPrimitive: TensorPrimitive;
    type Device: Device;
    // All tensor operations defined here
}
```

## burn-onnx Integration

### Compile-time Code Generation (Recommended)

**In build.rs:**
```rust
use burn_onnx::OnnxCodegen;

OnnxCodegen::new()
    .input("encoder.onnx")
    .output("src/inference/game/encoder.rs")
    .generate()?;
```

**Usage in code:**
```rust
let model: Model<NdArrayBackend> = Model::default();
let output = model.forward(input);
```

### Runtime Loading (Alternative)

```rust
use burn_onnx::OnnxModel;

let model = OnnxModel::new("model.onnx");
let output = model.forward(input);
```

## burn.toml Configuration

```toml
[model_exports]
default_backend = "ndarray"
default_device = "Cpu"

[ndarray]
```

## Common Patterns

### Neural Network Module

```rust
use burn::nn::{Linear, Module, ReLU};

#[derive(Module)]
struct MyModel {
    linear1: Linear<NdArrayBackend>,
    relu: ReLU,
    linear2: Linear<NdArrayBackend>,
}

impl MyModel {
    fn new() -> Self {
        Self {
            linear1: Linear::new(10, 20),
            relu: ReLU::new(),
            linear2: Linear::new(20, 2),
        }
    }
}
```

### Training Loop

```rust
use burn::optim::Adam;
use burn::loss::MseLoss;

let model = MyModel::new();
let mut optimizer = Adam::new();
let loss_fn = MseLoss::new();

for epoch in 0..10 {
    let output = model.forward(input);
    let loss = loss_fn.forward(&output, &target);
    let grads = loss.backward();
    optimizer.step(grads);
}
```

### Tensor Operations

```rust
// Shape operations
let reshaped = tensor.reshape([2, 3]);
let sliced = tensor.slice([0..2, 1..3]);
let transposed = tensor.transpose();

// Mathematical operations
let sum = tensor1 + tensor2;
let product = tensor1 * tensor2;
let matmul = tensor1.matmul(tensor2);
let softmax = tensor.softmax(dim);
```

## Project Integration

### Cargo.toml Setup

```toml
[dependencies]
burn = "0.21.0"
burn-ndarray = "0.21.0"
burn-onnx = "0.21.0"
```

### Build Script (build.rs)

```rust
use burn_onnx::OnnxCodegen;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    OnnxCodegen::new()
        .input("models/encoder.onnx")
        .output("src/inference/encoder.rs")
        .generate()?;
    
    Ok(())
}
```

## Best Practices

1. **Backend Selection**: Use `burn-ndarray` for development, `burn-wgpu` for production GPU
2. **ONNX Models**: Prefer compile-time code generation for better performance
3. **Device Management**: Always pass device reference explicitly
4. **Error Handling**: Use `anyhow` or `thiserror` for proper error types
5. **Compilation**: Enable optimizations in release mode for best performance

## When to Use

- Implementing deep learning models in Rust
- Integrating ONNX models into Rust applications
- Building high-performance ML pipelines
- Cross-platform ML deployments (CPU/GPU/embedded)
- Projects requiring memory safety and concurrency

## Version Compatibility

| Burn Version | Rust Edition | Key Features |
|--------------|--------------|--------------|
| 0.21.x | 2021 | Stable API, improved ONNX support |
| 0.20.x | 2021 | Tensor improvements, better WGPU support |

## Related Resources

- Official Docs: https://burn.dev/docs/
- GitHub: https://github.com/tracel-ai/burn
- Burn Book: https://burn.dev/books/burn/
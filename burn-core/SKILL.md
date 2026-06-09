---
name: "burn-core"
description: "Burn core framework - Provides tensor operations, automatic differentiation, and neural network building blocks for Rust deep learning."
---

# Burn Core Framework

## Overview

The core `burn` crate provides the fundamental building blocks for deep learning in Rust:

- **Tensor Abstraction**: Generic tensor types with backend support
- **Automatic Differentiation**: Type-safe autodiff system
- **Neural Network Modules**: Built-in layers and utilities
- **Optimizers**: Adam, SGD, AdamW and more
- **Loss Functions**: MSE, CrossEntropy, CTC, etc.

## Key Features

### 1. Tensor System

```rust
use burn::tensor::Tensor;
use burn_ndarray::NdArrayDevice;

let device = NdArrayDevice::default();
let tensor = Tensor::from_data(&[1.0, 2.0, 3.0], &device);
```

### 2. Automatic Differentiation

```rust
let x = Tensor::from_data(&[1.0, 2.0], &device).require_grad();
let y = x * 2.0;
let grads = y.backward();
```

### 3. Neural Network Module

```rust
use burn::nn::{Linear, Module, ReLU};

#[derive(Module)]
struct Model {
    linear: Linear<NdArrayBackend>,
    relu: ReLU,
}
```

### 4. Optimizers

```rust
use burn::optim::Adam;

let mut optimizer = Adam::new();
optimizer.step(grads);
```

## Core Components

| Component | Description |
|-----------|-------------|
| `burn::tensor` | Tensor operations and autodiff |
| `burn::nn` | Neural network layers |
| `burn::optim` | Optimization algorithms |
| `burn::loss` | Loss functions |
| `burn::data` | Data loading utilities |

## When to Use

- Building custom neural network architectures
- Implementing custom tensor operations
- Creating training pipelines
- Research and experimentation

## Related Crates

- `burn-ndarray`: CPU backend
- `burn-wgpu`: GPU backend
- `burn-onnx`: ONNX model import
---
name: "burn-onnx"
description: "Burn ONNX support - Import ONNX models into Burn for inference on any backend. Supports compile-time code generation and runtime loading."
---

# burn-onnx

## Overview

`burn-onnx` enables importing ONNX models into Burn, allowing them to run on any Burn backend (CPU, GPU, WebAssembly).

## Key Features

- **Compile-time Code Generation**: Convert ONNX to Rust code
- **Runtime Loading**: Load ONNX models at runtime
- **Multi-backend Support**: Run on any Burn backend
- **Automatic Optimization**: Benefit from Burn's optimizations

## Usage

### Compile-time Code Generation (Recommended)

**In build.rs:**

```rust
use burn_onnx::OnnxCodegen;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    OnnxCodegen::new()
        .input("model.onnx")
        .output("src/model.rs")
        .generate()?;
    
    Ok(())
}
```

**In your code:**

```rust
use burn_ndarray::NdArrayBackend;

mod model;
use model::Model;

let model: Model<NdArrayBackend> = Model::default();
let output = model.forward(input);
```

### Runtime Loading

```rust
use burn_onnx::OnnxModel;
use burn_ndarray::NdArrayBackend;

let model = OnnxModel::<NdArrayBackend>::new("model.onnx");
let output = model.forward(input);
```

### Multiple Models

```rust
// In build.rs
OnnxCodegen::new()
    .input("encoder.onnx")
    .output("src/encoder.rs")
    .generate()?;

OnnxCodegen::new()
    .input("decoder.onnx")
    .output("src/decoder.rs")
    .generate()?;
```

## burn.toml Configuration

```toml
[model_exports]
default_backend = "ndarray"
default_device = "Cpu"

[ndarray]
```

## Best Practices

1. **Prefer compile-time generation** for better performance
2. **Use runtime loading** for dynamic model loading
3. **Check operator support** before importing
4. **Optimize models** before conversion

## Operator Support

burn-onnx supports common ONNX operators:
- Arithmetic: Add, Sub, Mul, Div
- Linear: MatMul, Gemm
- Activation: Relu, Sigmoid, Tanh, Softmax
- Normalization: BatchNormalization, LayerNormalization
- Convolution: Conv, ConvTranspose

## Performance Comparison

| Mode | Performance | Flexibility |
|------|-------------|-------------|
| Compile-time | High | Low |
| Runtime | Medium | High |

## When to Use

- Importing pre-trained models
- Migrating from PyTorch/TensorFlow
- Cross-platform deployment
- WebAssembly inference

## Related Crates

- `burn`: Core framework
- `burn-ndarray`: CPU inference
- `burn-wgpu`: GPU inference
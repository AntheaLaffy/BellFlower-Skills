---
name: "burn-metal"
description: "Burn Metal backend - Apple GPU acceleration for macOS and iOS. Optimized for Apple Silicon and Intel-based Macs."
---

# burn-metal

## Overview

`burn-metal` provides Apple GPU acceleration using Metal. It's optimized for:

- **Apple Silicon**: M1, M2, M3 chips
- **Intel Macs**: With AMD or Intel integrated GPUs
- **iOS/iPadOS**: Mobile devices with Apple GPUs

## Key Features

- **Apple Metal Support**: Direct access to Metal API
- **Apple Silicon Optimization**: Optimized for ARM-based Macs
- **Unified Memory**: Shared memory between CPU and GPU on Apple Silicon
- **Cross-platform**: Works on macOS, iOS, iPadOS

## Usage

### Basic Setup

```rust
use burn::tensor::Tensor;
use burn_metal::MetalDevice;

// Create Metal device
let device = MetalDevice::default();

// Create tensor on GPU
let tensor = Tensor::from_data(&[1.0, 2.0, 3.0], &device);

// Metal-accelerated operations
let result = tensor.matmul(other_tensor);
```

### Backend Type

```rust
use burn_metal::MetalBackend;

type Backend = MetalBackend;
let model: Model<Backend> = Model::default();
```

### burn.toml Configuration

```toml
[model_exports]
default_backend = "metal"
default_device = "Gpu"

[metal]
```

## Requirements

- macOS 10.15+ or iOS 13+
- Apple GPU (Apple Silicon or Intel with integrated GPU)
- Xcode command line tools

## Best Practices

1. Use for Apple platform deployment
2. Leverage unified memory on Apple Silicon
3. Optimize for mobile on iOS
4. Use with Core ML integration

## Performance Considerations

- Excellent performance on Apple Silicon
- Unified memory reduces data transfer overhead
- Best for macOS/iOS applications
- Good for both training and inference

## When to Use

- macOS applications
- iOS/iPadOS applications
- Apple Silicon development
- Cross-platform Apple ecosystem apps

## Related Crates

- `burn`: Core framework
- `burn-wgpu`: Alternative cross-platform GPU backend
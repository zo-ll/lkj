# Requirements

## Core lkj

The Go core builds without Python dependencies.

## Whisper backend

The default `whispercpp` backend requires:

- `whisper-cli` from `whisper.cpp`.
- A compatible Whisper model file such as `ggml-base.en.bin`.

## Parakeet backend

The optional `parakeet` backend requires a Python environment with:

- PyTorch (`torch`).
- NVIDIA NeMo (`nemo`).
- Access to the configured Parakeet model, default `nvidia/parakeet-tdt-0.6b-v2`.

Caveat: your current `python3` does not have `torch` or `nemo` installed, so actual Parakeet transcription cannot run yet in this environment.

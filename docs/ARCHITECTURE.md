# StayTrace architecture

StayTrace is deliberately split into a deterministic evidence layer and an optional local multimodal reasoning layer.

## Deterministic layer

- OpenCV image normalization and alignment
- ORB feature matching with homography where enough features exist
- SSIM-based structural comparison
- morphological difference masks
- candidate-region extraction
- SQLite persistence
- PDF/JSON reporting

## AI layer

- Qualcomm GenieX VLM adapter for multimodal observations
- configurable model identifier and device map
- conservative fallback to deterministic descriptions when the runtime is not available

## Why this split exists

A VLM should explain and structure visual evidence, not become the sole decision-maker for whether two photographs are identical or whether someone is legally responsible for damage. Deterministic CV produces candidate changes; AI interprets them; the application reports uncertainty and keeps evidence links.

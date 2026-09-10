# Snapdragon validation plan

This document is intentionally a validation plan, not a fabricated benchmark report.

## Target

Validate on an actual supported Snapdragon Windows ARM64 machine. The Qualcomm GenieX project currently documents Windows ARM64 support on Snapdragon compute platforms and exposes both a QAIRT/NPU path and a llama.cpp path.

## Current VLM candidate

`ai-hub-models/Qwen3-VL-4B-Instruct`

The Qualcomm AI Hub model page currently lists Snapdragon X Elite and Snapdragon X2 Elite as supported devices and provides a GenieX QAIRT quick-start command. The same page currently shows an inconsistent top-level "Not supported" Compute status, so acceptance must be based on actual runtime execution rather than that badge alone.

## Validation checklist

1. Confirm `platform.machine()` reports ARM64 on the target Windows system.
2. Install the Qualcomm GenieX distribution appropriate to the backend.
3. Run `geniex devices` and record available plugins/devices.
4. Pull or resolve the exact VLM artifact.
5. Run a single-image inference from the command line.
6. Run the same image through StayTrace's `GenieXReasoner`.
7. Record warm and cold latency over repeated trials.
8. Record generated tokens/second when available from GenieX output profiles.
9. Record memory and any NPU/compute-unit details exposed by the environment.
10. Verify that the normal analysis workflow uses no cloud API.

## Acceptance criteria

- Model loads successfully.
- Image input is accepted by the runtime.
- Output can be parsed into the StayTrace observation schema or safely routed to manual review.
- The app can recover to deterministic CV if the VLM is unavailable.
- No benchmark value is inserted into the pitch until it is actually measured.

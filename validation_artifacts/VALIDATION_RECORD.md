# StayTrace Validation Record

Validated from the current repository source on 29 September 2026.

## Automated tests

`6 passed`

## Controlled fixture analysis

- Alignment method: `orb-homography`
- Alignment confidence: `0.9626`
- Difference score: `0.0263`
- Changed area ratio: `0.0425` (4.25%)
- Candidate regions: `5`
- Largest bounding box: `(427, 277, 197, 197)`
- Deterministic fallback finding: `change candidate / uncertain`
- Fallback confidence: `0.614`
- Manual review required: `true`

## Generated artifacts

- `difference_heatmap.jpg` - produced by `compare_images()`
- `evidence_report.pdf` - produced by `build_report()` and rendered successfully
- `cv_validation_result.json` - structured output record
- `validation_console.png` - rendered copy of the recorded command output

## Qualcomm status

The Qualcomm/Snapdragon path is implemented as an optional GenieX adapter but was not physically validated on a Snapdragon device in this environment. No Snapdragon performance number is claimed in this record.

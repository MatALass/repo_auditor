# Manual Review Workflow

This workflow exists to validate two critical outputs of the batch auditor:

- detected repository type
- suggested portfolio decision (`archive`, `rebuild`, `improve`, `keep`)

## Why this step matters

The batch summary is still heuristic.  
It is useful, but it is not yet trustworthy enough to be treated as ground truth.

Manual review is the bridge between:
- rule-based automation
- defensible portfolio decisions

## Input artifact

The review queue is exported from `batch-summary.json`.

Example:

```powershell
python .\scripts\export_review_queue.py .\reports\batch-summary.json
# Phase 7: Adaptive Behavior

## Summary

This phase adds user feedback capture and basic adaptive behavior to the banking support agent.

## Implementation

- Added `feedback_manager.py` with `FeedbackManager`:
  - Records ratings and optional comments.
  - Persists feedback to `feedback_log.json`.
  - Computes average rating and low-rating counts.
  - Recommends response adjustment directions based on aggregated feedback.

- Extended `agent_service.py`:
  - Prompts users for optional rating after answered queries.
  - Records feedback and returns adaptive guidance text.
  - Uses feedback to detect if the agent should simplify language or reinforce safety boundaries.

## Output & Observations

- Explicit feedback is captured without user PII.
- Early adaptation guidance is now available if average ratings decline.
- The system remains safe by avoiding automated behavioral changes that could alter scope boundaries.
- Observed that feedback logging supports continuous improvement and engineering review.

## Files Added

- `feedback_manager.py`

## Notes

- Feedback is stored separately from conversation logs to avoid mixing performance metrics with customer data.
- The agent uses feedback only for human-readable improvement recommendations.

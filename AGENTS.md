# Demo development rules

- Read TASK.md before starting.
- Complete one task per invocation, then stop.
- Change only files inside this daedalus-sandbox repository.
- Inspect actual machine state before reporting facts.
- Never invent checks, results, deployments, or completed work.
- Keep the page self-contained with no external dependencies.
- Preserve Cycle 0 and every existing journal card.
- Append a separate article card for each completed change.
- Give each card a unique cycle number and actual ISO 8601
  data-created-at timestamp including its timezone offset.
- Include a matching time element with a datetime attribute.
- Display dates in America/Chicago, including timezone abbreviation.
- Keep Oldest First as the default and sort by creation timestamp.
- Record what changed, verification results, and the next task.
- Update TASK.md for the next invocation.
- Stage only specific demo files; exclude unrelated changes and secrets.
- Report the commit ID and verification performed.
- Do not claim remote preservation unless the push was verified.
- Do not initiate provisioning or shutdown; Athena controls those steps.

## Pull request workflow
- Start each task from the latest origin/main on a new daedalus/* branch.
- Commit and push only the task branch.
- Open a pull request targeting main and request graystone-john's review.
- Include the changes, actual verification results, and next task.
- Never push directly to main, merge your own pull request, or bypass rules.
- Do not initiate provisioning; wait for the approved revision.
- You may read ../ai-forge and ../ai-stores for context and cite their
  file paths and commit IDs. Keep edits inside this sandbox repository.

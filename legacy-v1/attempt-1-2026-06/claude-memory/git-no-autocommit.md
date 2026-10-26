---
name: git-no-autocommit
description: User preference — never git commit in this project unless explicitly told to; just save files to the working tree
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bb4fecd9-8007-463d-929c-12a9ff9da5e0
---

In this project (tud-analog-cmos-design-2), **do NOT run `git commit` unless the user
explicitly asks**. Finish the work, save all files to the working tree, and stop there —
let the user review and commit themselves.

**Why:** On Phase 3 I committed proactively (reasoning from the "Phases 1–2 are DONE,
verified, and committed" framing + "do it fully and completely"). The user reset it
(`git reset --soft`) and said "dont commit unless i tell u so next time." The prior
phases being committed does NOT imply standing authorization to commit new ones.

**How to apply:** Treat "produce and save the results" as write-files-only. When work is
complete, summarize and offer to commit, but wait for an explicit go-ahead. This overrides
any general per-phase-commit pattern inferred from git history.

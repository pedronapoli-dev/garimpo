---
name: slice
description: Drives the implementation of one Garimpo delivery slice, from plan to passing tests, in learning mode. Use when Pedro asks to start or continue a slice.
argument-hint: [slice-number]
disable-model-invocation: true
---

Drive slice $ARGUMENTS from `docs/requirements.md`.

1. Read `docs/requirements.md` and the current state of the code. If the previous slice is not done (failing or missing tests), stop and say what is missing.
2. Present a plan of 3 to 7 steps. Each step ends in something testable. List the Python or React Native concepts the slice introduces. Wait for Pedro to approve.
3. For each step:
   - Explain each new concept by comparing it with Swift, in at most one paragraph and one code snippet.
   - Write the test first, or ask Pedro to write it, according to the working mode in CLAUDE.md.
   - Provide the skeleton with `TODO` markers and wait for Pedro to implement it.
   - Review what Pedro wrote, pointing out Swift habits.
   - Run tests, lint and format. Move on only when everything passes.
   - Suggest a commit message in English, in the imperative mood.
4. When the slice is done, summarize in up to 5 lines what was learned and what moves to the next slice.

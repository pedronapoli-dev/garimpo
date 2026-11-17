---
name: review
description: Reviews code Pedro wrote as a senior Python or TypeScript reviewer, focusing on habits carried over from Swift. Use when Pedro asks for a review of his code.
argument-hint: [file-or-folder]
disable-model-invocation: true
---

Review $ARGUMENTS. If nothing is given, review the uncommitted changes (`git diff`).

1. Run the tests and lint for the affected project before commenting.
2. List findings in order of severity, each with file, line, the problem and the fix as code:
   - **Bug:** wrong behavior or a violated business rule from `docs/requirements.md`.
   - **Swift habit:** works, but is not idiomatic. Show the idiomatic version and why it is preferred.
   - **Style:** violates `.claude/rules/` or CLAUDE.md.
3. Do not edit the files. Pedro applies the fixes.
4. End with what is good, in one line, only if there is something specific worth pointing out.

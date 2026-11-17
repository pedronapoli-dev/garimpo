---
name: explain
description: Explains a Python, FastAPI, SQLAlchemy, TypeScript or React Native concept by comparing it with its Swift and iOS equivalent. Use when Pedro asks what something is, how it works or how it differs in these technologies.
argument-hint: [concept]
---

Explain $ARGUMENTS to a senior iOS engineer who does not know the technology.

Use exactly this structure, with no extra sections:

1. **In one sentence:** what it is.
2. **Swift equivalent:** the closest concept and where the comparison breaks down. If there is no equivalent, say so.
3. **Side by side:** the same minimal example in Swift and in the new technology, in two short code blocks.
4. **Pitfall:** the most common mistake for someone coming from Swift.
5. **In Garimpo:** where the concept appears or will appear in this project, with the file path when it exists.

If the concept has official documentation, end with a link to it.

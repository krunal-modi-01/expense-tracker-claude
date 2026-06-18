---
description: Create a commit message by analyzing git diffs
allowed-tools: Bash(git status:*), Bash(git diff --staged), Bash(git commit:*)
---

## Your task:

Analyze above staged git changes and create a commit message. Use present tense and explain "why" something has changed, not just "what" has changed.

## Run these commands:

```bash
git status
git diff --staged
```

## Format
Use the following format to form the commit message:

```
<type>: <concise_description>
<optional_body_explaining_why>
```

## Output:

1. Show summary of changes currently staged.
2. Propose commit message
3. Ask for confirmation before committing.

DO NOT auto-commit - wait for user approval, and only commit if the user says so.

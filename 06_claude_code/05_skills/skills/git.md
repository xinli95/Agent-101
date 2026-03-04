# Git Conventions

## Commit Messages
- Use imperative mood: "Add feature" not "Added feature"
- First line max 72 chars; leave blank line before body
- Reference issues: "Fix login bug (closes #42)"

## Branch Strategy
- `main` — production-ready only, never commit directly
- `feat/<name>` — new features
- `fix/<name>` — bug fixes
- `chore/<name>` — tooling, deps, refactoring

## Workflow
```bash
git checkout -b feat/my-feature
# make changes
git add -p                    # stage hunks interactively
git commit -m "Add my feature"
git push -u origin feat/my-feature
# open PR → squash merge into main
```

## Useful Commands
```bash
git log --oneline -10         # recent commits
git diff --staged             # review staged changes before commit
git stash                     # shelve uncommitted changes
git rebase -i HEAD~3          # interactive rebase last 3 commits
```

# Repository Sync Strategy

This document describes the bidirectional sync strategy between the private and public claude-cookbooks repositories.

## Branch Structure

### Private Repository (`claude-cookbooks-private`)

**`main`**: Workflow storage branch
- Contains sync workflows: `push-to-public.yml`, `pull-from-public.yml`
- No active development happens here
- Workflows run from this branch

**`staging`**: Active development branch
- All PRs target this branch
- Contains CI/test workflows (e.g., linting, tests, builds)
- Diverges from `public` until release time

**`public`**: Public-facing branch
- Mirrors the public repository
- Contains CI/test workflows (same as staging)
- Does NOT contain sync workflows
- Automatically syncs with public repo

### Public Repository (`claude-cookbooks`)

**`main`**: Public main branch
- Receives external contributions via PRs
- Syncs bidirectionally with private `public` branch

## Workflow Process

### Internal Development (Private PRs)

1. **Open PR** against `staging` branch
2. **CI runs** (tests, linting from `staging` workflows)
3. **Merge** to `staging`
4. `staging` and `public` diverge

### Releasing to Public

1. **Open PR** from `staging` → `public` (in private repo)
2. **Review changes** - this is your "release gate"
3. **Resolve conflicts** if any (from external PRs that came into `public`)
4. **Merge** `staging` → `public`
5. **Automatic push**: `push-to-public.yml` triggers and pushes `public` branch to public repo

### Post-Release: Syncing staging (Manual)

After a major release, you can optionally reset `staging` to match `public` to prevent long-term divergence:

```bash
git fetch origin
git checkout staging
git reset --hard origin/public
git push --force origin staging
```

**When to reset:**
- ✅ After major releases when you want a clean slate
- ✅ When `staging` and `public` have diverged significantly
- ❌ Not needed for quick bugfixes or hotfixes
- ❌ Skip if there are active feature branches

**Benefits of manual reset:**
- More flexibility for bugfixes on `staging` without triggering releases
- Control over when to force-push shared branch
- Can coordinate with team before resetting

**⚠️ Important**: When resetting:
- Any open PRs or feature branches based on old `staging` will need to be rebased
- Communicate to team before resetting
- Check for open PRs first

### External Contributions (Public PRs)

1. **PR opened** on public repo
2. **Merge** to public repo `main`
3. **Scheduled sync**: `pull-from-public.yml` runs (daily at 2 AM UTC)
   - Pulls changes from public repo
   - Merges into private `public` branch
   - Pushes to private repo
4. **On next release**: Conflicts resolved when merging `staging` → `public`

## Automation Details

### push-to-public.yml

**Trigger**: Push to `public` branch (or manual)

**What it does**:
- Checks out private `public` branch
- Pushes to public repo `main`
- Creates issue on failure

### pull-from-public.yml

**Trigger**: Daily schedule (2 AM UTC) or manual

**What it does**:
- Checks out private `public` branch
- Fetches from public repo
- Merges public repo `main` into private `public`
- Creates issue on merge conflicts

## Key Principles

✅ **`staging` and `public` can diverge** - conflicts resolved at release time
✅ **Optional manual reset** - reset `staging` to `public` when needed for clean slate
✅ **Standard merge workflow** - no manual rebasing during development
✅ **Clear release gate** - the PR from `staging` → `public`
✅ **Flexible for bugfixes** - can work on `staging` without triggering releases
✅ **Sync workflows isolated** - only in `main`, not in public branches

## Handling Feature Branches

### If staging is reset (manual operation):

When `staging` is manually reset to match `public`, developers with feature branches need to rebase:

**Option 1: Rebase your branch** (recommended)
```bash
git checkout your-feature-branch
git fetch origin
git rebase origin/staging
git push --force-with-lease
```

**Option 2: Merge the new staging**
```bash
git checkout your-feature-branch
git fetch origin
git merge origin/staging
git push
```

### Best Practices:
- Communicate before resetting `staging` to coordinate with team
- Check for open PRs before resetting
- Keep feature branches short-lived
- Use `git push --force-with-lease` when force-pushing (safer than `--force`)
- Consider not resetting if there are many active feature branches

## Initial Setup

To set up this workflow for the first time:

1. **Ensure workflows are in `main`**:
   ```bash
   git checkout main
   # Verify workflows exist
   ls .github/workflows/
   ```

2. **Create `staging` branch** from current main:
   ```bash
   git checkout -b staging main
   git push origin staging
   ```

3. **Create `public` branch** from staging, removing sync workflows:
   ```bash
   git checkout -b public staging
   git rm .github/workflows/push-to-public.yml
   git rm .github/workflows/pull-from-public.yml
   git commit -m "Remove sync workflows for public branch"
   git push origin public
   ```

4. **Initial sync** to public repo:
   ```bash
   # Manually trigger push-to-public workflow
   # Or use GitHub CLI:
   gh workflow run push-to-public.yml
   ```

## Troubleshooting

### Merge conflicts on staging → public PR

**Cause**: External changes came into `public` that conflict with `staging` work.

**Resolution**:
- Resolve conflicts in the PR
- This is expected and part of the release process

### Feature branch out of sync after staging reset

**Cause**: `staging` was manually reset to match `public`.

**Resolution**:
- Rebase your feature branch on the new `staging`
- See "Handling Feature Branches" section above

### Staging and public diverging too much

**Cause**: Multiple releases without resetting `staging`, or many external PRs.

**Resolution**:
- Manually reset `staging` to match `public` (see "Post-Release: Syncing staging" section)
- Coordinate with team before resetting
- Future PRs will have cleaner merges

### Push to public fails

**Cause**: Divergent history, concurrent changes, or permissions.

**Resolution**:
- Check workflow logs for specific error
- Verify public repo state
- Manual sync if needed: `git push public public:main`

### Pull from public conflicts

**Cause**: Changes in private `public` branch conflict with public repo.

**Resolution**:
- Follow instructions in auto-created issue
- Manually merge and resolve conflicts
- Push resolved version

## Benefits of This Approach

✅ **Simple and maintainable** - no complex cherry-picking during development
✅ **Flexible divergence management** - manual reset when needed, not forced
✅ **Clear release process** - explicit PR acts as gate
✅ **Bidirectional sync** - handles both internal and external contributions
✅ **Conflict resolution at natural point** - during release, not constantly
✅ **Supports bugfix workflows** - can work on staging without triggering full releases
✅ **Standard git workflow** - familiar to most developers
✅ **Controlled force pushes** - team coordination when resetting staging

# Hand-off: populate `trivoallan/regis-action`

This directory holds the full initial content of the dedicated action repo
[`trivoallan/regis-action`](https://github.com/trivoallan/regis-action), which
was **created** during the extraction session but could **not be pushed to**
because the session's MCP repository scope was limited to `trivoallan/regis`.

> ⚠️ This `regis-action-staging/` directory is a **temporary hand-off**. It is
> not part of the core `regis` package and should be removed from the core
> repository once the new repo is populated.

## Push the content

From a checkout of this branch:

```bash
# 1. Clone the (empty, auto-initialised) new repo somewhere separate
git clone https://github.com/trivoallan/regis-action.git /tmp/regis-action

# 2. Copy the staged content over (including dotfiles)
cp -a regis-action-staging/. /tmp/regis-action/
rm -f /tmp/regis-action/PUSH.md

# 3. Commit and push
cd /tmp/regis-action
git add -A
git commit -m "feat: bootstrap regis-action repository"
git push origin main
```

## After pushing — manual setup

1. **Secrets / CI token**: add an App token or PAT so release-please PRs
   trigger downstream CI (the default `GITHUB_TOKEN` cannot), mirroring
   `regis-dashboard` (`RELEASE_PLEASE_TOKEN`). Wire it into
   `.github/workflows/release-please.yml`.
2. **Branch protection** on `main`.
3. **Initial release**: cut `v1.0.0` (release-please) so `tag-major.yml` creates
   the floating `v1` tag and `uses: trivoallan/regis-action@v1` resolves.
4. **Marketplace**: publish the action from the new repo's `v1.0.0` release.
5. **Verify** end-to-end with a `uses: trivoallan/regis-action@v1` run.

## Then clean up the core repo

```bash
git rm -r regis-action-staging
git commit -m "chore(ci): remove regis-action hand-off staging directory"
```

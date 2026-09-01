# Releasing

This project uses [Semantic Versioning](https://semver.org/): given `MAJOR.MINOR.PATCH`,
bump

- **MAJOR** for a change that breaks existing deployments (config that must change, a
  removed feature, incompatible behavior),
- **MINOR** for backwards-compatible new features,
- **PATCH** for backwards-compatible bug fixes only.

The package version is **derived from the Git tag** by
[setuptools-scm](https://setuptools-scm.readthedocs.io/) — there is no version string to
edit. Tag `v1.2.3` produces version `1.2.3`; commits after a tag report a development
version such as `1.2.4.dev5+g<sha>`.

The changelog is assembled from *news fragments* by
[scriv](https://scriv.readthedocs.io/).

## During development: add a news fragment to every user-facing PR

```bash
pip install -e '.[dev]'      # once, to get the scriv CLI
scriv create                 # writes changelog.d/<timestamp>_<branch>.md
```

Edit the new file: keep only the relevant `###` section(s) (Backwards-incompatible
changes / New features / Bug fixes / Other changes), delete the rest, and write one short
past-tense bullet per change. Commit it with the PR. Fragments accumulate in
`changelog.d/` and stay out of each other's way, so parallel PRs never conflict on the
changelog.

Purely internal changes (refactors, CI, tests) don't need a fragment.

## Cutting a release

1. Make sure `main` is green (CI) and you're up to date:

   ```bash
   git checkout main && git pull
   ```

2. Pick the new version `X.Y.Z` based on the fragments in `changelog.d/`. Collect them
   into `CHANGELOG.md`:

   ```bash
   pip install -e '.[dev]'
   scriv collect --version X.Y.Z
   ```

   This writes a new dated section at the top of `CHANGELOG.md` and deletes the
   fragment files. Review the result and tidy the wording.

3. Commit the changelog on a short branch and open a PR:

   ```bash
   git checkout -b release/X.Y.Z
   git add CHANGELOG.md changelog.d/
   git commit -m "Release X.Y.Z"
   git push -u origin release/X.Y.Z
   ```

4. Once that PR is merged, tag the merge commit on `main` and push the tag:

   ```bash
   git checkout main && git pull
   git tag -a vX.Y.Z -m "Release X.Y.Z"
   git push origin vX.Y.Z
   ```

   Tags carry a `v` prefix (`vX.Y.Z`) — that is the pattern
   `.github/workflows/docker.yaml` triggers on. Pushing the tag builds and
   pushes `ghcr.io/lsst-so/so-slackbot-evening-tailgate:X.Y.Z` (and `:X.Y`),
   which is what Phalanx pins.

5. Optionally create a GitHub Release from the tag, pasting in that version's section of
   `CHANGELOG.md`. `scriv github-release` can do this for you.

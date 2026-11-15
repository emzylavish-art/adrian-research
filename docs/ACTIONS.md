# Actions diagnosis

The two-second failures are not a missing key and not a test failure. The job never reaches a runner, so no step and no log exist to read.

## What the failed runs show

Checked run `43720338417` on `main`, workflow `.github/workflows/ci.yml`, job `unit`:

- Started `2026-11-15T13:41:49Z`, completed `2026-11-15T13:41:51Z`.
- Conclusion `failure`.
- `steps` is empty.
- `runner_name` and `runner_group_name` are empty.
- The log blob does not exist. The Actions log API returns `BlobNotFound`.
- Repository Actions are enabled and `allowed_actions` is `all`.
- The same shape repeats on earlier CI runs for this private repository.

`ci.yml` does not read `SOCIALFETCH_API_KEY` or `EASYDOWN_API_KEY`. A missing secret cannot be why that job dies. The integration workflow was not the failing run.

This matches GitHub's own report of hosted jobs that fail before runner allocation: empty steps, no "Set up job", no logs, and a finish in two or three seconds. The public note is [discussion 207926](https://github.com/orgs/community/discussions/207926). The usual account cause on a private repository is a billing or spending-limit block, or an account-level Actions suspension. Community support cannot re-enable that. The account owner has to check Settings, then Billing and plans, then Actions minutes and the spending limit, or ask GitHub Support with the run URL.

No workflow file can allocate a runner that GitHub refuses to start. A YAML change will not turn run `43720338417` green.

## Secret-gated workflow

GitHub does not allow `secrets` in a job-level `if`. A job that wants to read a secret must request a runner first. That is why the old Integration workflow started a `keys` job on `ubuntu-latest` even when both secrets were absent. On this account that job dies in two seconds and the workflow is red, instead of skipped.

The patched Integration workflow does not request a runner unless the dispatch input for that backend is turned on. A plain dispatch therefore skips both jobs with no machine. If the input is on and the matching secret is still empty, the job prints the skip line and exits 0 before checkout, pip, or the API. A missing key is not a failed live call. A present key that fails `whoami` or parse is still a failure.

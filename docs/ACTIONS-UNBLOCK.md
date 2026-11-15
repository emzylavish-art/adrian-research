# Private-repo Actions unblock

Run `43720338417` died before a runner existed. Do not re-run the unit job until the checks below are true. A second run with the same account block fails the same way: about two seconds, empty steps, empty runner name, and no log blob.

The failing job is `unit` in `.github/workflows/ci.yml`. It does not read `SOCIALFETCH_API_KEY` or `EASYDOWN_API_KEY`. Adding those secrets will not start this runner.

## Checks, in order

1. Open https://github.com/emzylavish-art/tiktok-research-mcp/actions/runs/43720338417 and confirm the annotation. The expected text is that the job was not started because payments failed or the spending limit must be increased. If the page instead names a workflow syntax error, stop and fix that file. Do not treat a billing annotation as a test failure.
2. Open https://github.com/settings/billing/actions for the account `emzylavish-art`. Confirm Actions is not disabled for the account, the included private-repo minutes are not exhausted, and the spending limit is not `$0` if included minutes are gone. A private repository does not get the unlimited public-repo allowance.
3. Open the repository Settings, then Actions, then General. Confirm Actions is allowed and the allowed-actions policy is not blocking `actions/checkout` or `actions/setup-python`. The API already reported `enabled: true` and `allowed_actions: all` on 15 November 2026. Re-check it anyway before a rerun, because an owner can change it.
4. Confirm the repository is still private. If it is private and billing is blocked, making it public is a separate decision. Do not make it public only to obtain a runner.
5. If steps 2 and 3 are clean and a new hosted job still dies in two seconds with no steps, stop rerunning. Ask GitHub Support with account `emzylavish-art`, run URL https://github.com/emzylavish-art/tiktok-research-mcp/actions/runs/43720338417, and the fact that `runner_name` was empty and the log API returned `BlobNotFound`. Community comments cannot re-enable the account.

## Re-run only after those checks pass

```bash
gh run rerun 43720338417 --repo emzylavish-art/tiktok-research-mcp --failed
```

A successful rerun has a non-empty `runner_name`, a "Set up job" step, and a log. Until that happens, the unit job is not evidence about the tests. Local proof remains:

```bash
PYTHONPATH=. python -m pytest -q
```

That local run is not a substitute for the tag gate in [RELEASE-OPERATOR.md](RELEASE-OPERATOR.md).

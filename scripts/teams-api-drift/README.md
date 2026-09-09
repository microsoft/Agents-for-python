# Teams API drift detection

This tooling compares public `microsoft-teams-api` contracts with recorded usage in
`microsoft-agents-hosting-msteams`; it does not automatically change SDK code or
adopt upstream features. The extension pins one exact Teams API version so every
upgrade is reviewed and tested explicitly.

## Run locally

Use Python 3.12 so manual comparisons can include historical releases such as
`microsoft-teams-api==2.0.0`, which requires Python 3.12. `TEAMS_API_PYTHON` can
specify a different interpreter for the disposable extraction and test
environments when needed.

```bash
python -m pip install -r scripts/teams-api-drift/requirements.txt
python scripts/teams-api-drift/teams-api-drift.py compare --from 2.0.16 --to CANDIDATE_VERSION --work-root .teams-api-comparison --output artifacts/teams-api-drift/example
python scripts/teams-api-drift/teams-api-drift.py prepare-candidate --version CANDIDATE_VERSION --environment .teams-api-comparison/candidate --output artifacts/teams-api-drift/example
./.teams-api-comparison/candidate/bin/python -m mypy --config-file scripts/teams-api-drift/mypy.ini tests/teams_api_drift/test_contracts.py
./.teams-api-comparison/candidate/bin/python -m pytest tests/hosting_msteams -o asyncio_default_fixture_loop_scope=function
python scripts/teams-api-drift/teams-api-drift.py verify-usage
python scripts/teams-api-drift/teams-api-drift.py detect --comparison artifacts/teams-api-drift/example/raw-api-diff.json --output artifacts/teams-api-drift/example --fail-on-drift
python scripts/teams-api-drift/teams-api-drift.py summary --build success --usage-collection success --api-extraction success --api-comparison success --contract-tests success --boundary-tests success --candidate-environment artifacts/teams-api-drift/example/candidate-environment.json --output artifacts/teams-api-drift/example
python scripts/teams-api-drift/teams-api-drift.py render --findings artifacts/teams-api-drift/example/findings.json --test-summary artifacts/teams-api-drift/example/test-summary.json --output artifacts/teams-api-drift/example
```

Replace `CANDIDATE_VERSION` with the exact release being evaluated.

Omit `--to` to query the latest stable, non-yanked PyPI release. Omit `--from` to
use the version installed in the calling interpreter. Each comparison installs
exact upstream versions in separate virtual environments. `--work-root` keeps the
candidate environment after extraction so the following build and compatibility
commands test that exact version. An unsupported interpreter or unresolved
dependency is a failed extraction, never evidence of an unchanged API. On
Windows, use `.teams-api-comparison\candidate\Scripts\python.exe`.

Each command has one bounded role and reads its inputs from arguments. The GitHub
Actions workflows compose these commands, record step outcomes, decide whether
Copilot and publication are allowed, upload evidence, and enforce the final
result. No Python command reads the GitHub event, publishes comments/issues, or
implements workflow policy. Run `teams-api-drift.py --help` to list subcommands
and append `--help` after a subcommand for its options.

## Evidence and classification

- `baseline-api.json` / `candidate-api.json`: normalized public exports, methods,
  constructors, types and Pydantic fields, plus interpreter/extractor versions
  and the complete resolved package inventory.
- `raw-api-diff.json` / `teams-api.diff`: structured changes with deterministic
  `TSAPI-*` IDs and a readable diff excluding extraction metadata.
- `findings.json`: direct usage, affected source files, exposure, capability,
  evidence and classification for each upstream change.
- `test-summary.json` and `deterministic-report.md`: actual build and candidate
  verification outcomes. Failed extraction still produces an explicitly incomplete
  deterministic report from the evidence that is available.
- `agent-context.json`, `agent-report.md`, `agent-report-validation.json`: bounded
  input, advisory output and mechanical validation results when AI runs.

Consumed removals and incompatible public contracts block adoption. Internal
contract changes require adaptation. Additive capabilities and uncertain changes
are for review; unrelated changes need no action. `--fail-on-drift` returns 1 for
blocking/required findings **after** writing the findings artifact. API extraction
does not compare method bodies: runtime checks cover selected behavioral contracts.

The classifier and context command accept `--public-api-report` using the source
port's schema (`package`, `status`, `publicSymbolChanges`, `upstreamTypeLeaks`).
Producing that separate extension public API baseline is outside this pipeline.

## Maintain the usage map

Update the checked-in `teams-api-usage-manifest.json` when adding an upstream
import, reading/writing a model field, constructing a client/model or changing
public exposure. Use fully qualified **import paths**, package-relative files,
snake_case field names and nested paths such as `settings.selected_channel.id`.
Record construction/validation explicitly so new required fields are detected.
The coverage check rejects missing direct imports and paths outside the source
tree. This is a curated usage map, not automatic whole-program data-flow analysis.

The adjacent `config/teams-capabilities.yaml` maps upstream module areas to
feature owners and adoption policies. It supports strict compatibility,
review-new-members and advisory-only policies. It does not authorize adoption.

## Workflows

PRs to `main` or `release/*` run dependency analysis only when the exact Teams
version pin in `setup.py` changes. The base branch pin is the baseline and the PR
pin is the candidate. Manual PR-workflow dispatch takes explicit `from` and `to`
versions. The weekly workflow runs Monday at 08:00 UTC and compares the current
pin (currently 2.0.16) with the latest stable release, including future major
versions. Once maintainers approve an upgrade, changing the pin establishes the
new baseline. When the resolved versions are identical, manual and scheduled runs
finish successfully after version resolution; comparison, tests, reports, AI and
publication are skipped.

Candidate verification installs locally built wheels plus the exact selected
Teams version. A candidate that differs from the current pin is tested in
isolation without changing SDK metadata; the report identifies that difference.
The candidate's transitive dependencies, including `microsoft-teams-common`, are
recorded. Common's entire API is not compared; ClientOptions is covered by tests.

Trusted runs need `contents: read`, `copilot-requests: write`, and the applicable
`pull-requests: write` or `issues: write` permission. The repository/organization
must allow GitHub Copilot CLI requests using the workflow token. Copilot receives
only bounded deterministic evidence and relevant redacted source slices. Source
slices are capped at 12,000 characters per file and 12,000 characters in total;
the complete deterministic evidence remains in the uploaded artifact. Copilot is
denied tools. Its report never authorizes implementation. AI failures fail trusted
runs where AI is required. Fork PRs retain deterministic checks and artifacts
without AI/publication requirements.

GitHub documents the token permission in
[Using Copilot CLI in GitHub Actions](https://docs.github.com/en/enterprise-cloud%40latest/copilot/how-tos/copilot-cli/use-copilot-cli-in-actions).
Actionlint 1.7.12 does not yet recognize `copilot-requests`; when validating these
workflows with that release, ignore only `unknown permission scope "copilot-requests"`.
Keep all other permission and workflow checks enabled.

Artifacts are uploaded for 21 days before publication and the final policy gate.
Trusted PRs upsert one marker-based summary comment. Changed scheduled comparisons
upsert one open advisory issue only after report validation. An unchanged comparison
does not automatically close an existing issue. No separate implementation issues
are created. Tokens are not included in artifacts.

## Validate changes

```bash
python -m pytest tests/teams_api_drift -o asyncio_default_fixture_loop_scope=function
python -m mypy --config-file scripts/teams-api-drift/mypy.ini tests/teams_api_drift/test_contracts.py
python -m pytest tests/hosting_msteams -o asyncio_default_fixture_loop_scope=function
python -m black --check scripts/teams-api-drift tests/teams_api_drift tests/hosting_msteams/test_api_boundaries.py
```

Static contracts and Teams tests require the local activity, hosting-core,
authentication-msal and hosting-msteams packages plus the candidate installed.
Offline tests validate publication orchestration and registry metadata without
creating live comments or issues. On Windows, use a short environment path or
extended paths if the Graph dependency exceeds the system path-length limit.

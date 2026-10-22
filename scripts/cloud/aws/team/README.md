# Team AWS Cloud Deployment (skeleton)

One shared, account-agnostic set of scripts that deploys the whole
integrated app (all five stacks plus `unified-home`) to the team's AWS
account, region `ap-southeast-2`. **Student 4's stack is fully implemented
as the reference example.** Every other stack is a clearly marked
`TODO(owner: <student>)` in `deploy/services.yaml` - nobody needs to touch
the scripts themselves, only the manifest entry for their own stack.

This is a **skeleton**, not the finished group deployment: `deploy/services.yaml`
lists every student with `status: todo` except Student 4, and every script
skips a `todo` stack with a warning (or fails with `STRICT=true`) rather
than ever guessing a value.

Nothing in this folder has been run for real. Every script supports
`DRY_RUN=true`, which makes zero AWS calls and prints exactly what it
would do instead - that's how this skeleton was built and checked.

## How this folder is laid out

| File | Purpose |
|---|---|
| `config.env.example` | Copy to `config.env` (gitignored) and fill in `AWS_REGION`/`PROJECT_PREFIX`. |
| `common.sh` | Shared helpers every script sources: the `AWS_PAGER=""` fix, account confirmation, `DRY_RUN` support. |
| `deploy/services.yaml` | The manifest - one entry per stack, Student 4 filled in, everyone else `TODO`. |
| `deploy/manifest.py` | Read-only parser for the manifest (used by every script - never calls AWS). |
| `deploy/render_task_def.py` | Renders one stack's ECS task definition + Service Connect config as JSON. |
| `env-setup.sh` | One-time (safe to re-run): ECS service-linked role, networking, security group, Service Connect namespace. |
| `build-and-push-images.sh` | Builds and pushes one ECR image per container, for every `ready` stack. |
| `deploy.sh` | Registers task definitions and creates/updates one ECS service per `ready` stack. |
| `deployment-test.sh` | Checks each `ready` stack's task is running, records AI-flag values into `reports/cloud/deployment-results.md`. |
| `cleanup.sh` | Tears down everything the above created, for every stack name (asks for typed confirmation). |
| `bootstrap.sh` + `bootstrap/oidc-role.yaml` | Team-lead-only, one-time: GitHub OIDC provider + the role Actions assumes. |

## TODO table - who needs to add what

| Owner | File | What to add |
|---|---|---|
| Student 1 - Andy | `deploy/services.yaml` (`student1` entry) | Dockerfile paths for database/backend/frontend; confirm database's real container port; decide `ingress` (see note below). |
| Student 1 - Andy | `student-1-Andy-Lam/frontend/` (no nginx.conf exists) | Add an nginx reverse-proxy `location` block (copy Student 4's `nginx/default.conf.template` pattern) so the frontend can go `internal` instead of needing a public backend. Currently `js/config.js:3` hardcodes an absolute `http://127.0.0.1:5001` fallback that only works if the backend itself is public. |
| Student 2 - Hein | `deploy/services.yaml` (`student2` entry) | Dockerfile paths; confirm `allocation-database`'s container port (6002, per `docker-compose.yml`); decide `ingress`. |
| Student 2 - Hein | `student-2Hein-Htet-Aung/frontend/` (no nginx.conf exists) | Same as Student 1 - add a reverse-proxy block. `js/config.js:2` currently hardcodes an absolute `http://localhost:5002` fallback. |
| Student 3 - Tristan | `deploy/services.yaml` (`student3` entry) | Dockerfile paths; decide `ingress`. |
| Student 3 - Tristan | `student-3Tristan-Lim/frontend-service/nginx.conf` | Has no `proxy_pass` block at all yet (confirmed - it's `location / { try_files ...; }` only). Add one, same pattern as Student 4's. `js/config.js:3` and `docker-entrypoint.sh:6,9` currently set an absolute `http://localhost:5003`. |
| Student 3 - Tristan | (separate from this manifest) | Your own multi-agent integration (`routes/multi_agent_mode.py`, `templates/tabs/multi-agent.html`) exists on your personal branch (`1efc54b`) but isn't merged into `main` yet - higher priority than this cloud manifest. |
| Student 5 - Matthew | `deploy/services.yaml` (`student5` entry) | Dockerfile paths; decide `ingress`. |
| Student 5 - Matthew | `student-5Matthew-Barnard/frontend-service/nginx.conf:6` | `resolver 127.0.0.11 valid=10s ipv6=off;` - this is Docker Compose's embedded DNS address, hardcoded. It will 502 on Fargate for the exact reason Student 4's did (see troubleshooting below). Fix: read the real nameserver from `/etc/resolv.conf` at container startup instead, same fix already applied in `student-4Nicholas-Hatzidimitriou/frontend/docker-entrypoint.sh`. |
| Student 5 - Matthew | (separate from this manifest) | No Release 2 work exists yet on your branch for multi-agent, pre-commit, or endpoint-test evidence - higher priority than this cloud manifest. |
| Team lead | `deploy/services.yaml` (`unified-home` entry) | Needs a real Dockerfile (currently a bind-mounted `nginx:alpine` in `docker-compose.yml`, not buildable as a standalone image yet) and proxy routes to each student's frontend, once every student has decided their own `ingress`. |
| Team lead | `shared/frontend/index.html:24,31,38,45,52` | Hardcodes `http://localhost:8001` through `:8005` for every student's frontend link. Needs to become relative proxy routes once `unified-home`'s own entry above is filled in. |
| Team lead | `env-setup.sh` | Creates one shared *internal* security group only. No public ALB or its security group exists yet - add once `unified-home`'s ingress design is settled. |
| Team lead | `bootstrap/oidc-role.yaml` | Trust policy's allowed ref/branch, and the permission set (deliberately `Resource: "*"` right now) both need review before this is deployed for real - see the file's own `TODO` comments. |
| Team lead | `.github/workflows/cloud-deployment.yml` | Decide whether `validate` should also bring up the local compose stack and run post-commit tests (see the job's own `TODO` comment); confirm whether a `production` GitHub Environment should gate the `deploy` job. |

**Ingress decision, asked of every student above:** each of your frontends
currently writes an *absolute* backend URL (`API_BASE`/`BACKEND_URL`) into
a JS file at container startup, and calls the backend directly,
cross-origin. That works today because your backend is reachable at that
address. In this design, every backend is `internal` (not publicly
reachable) - so either (a) add a reverse-proxy block to your own frontend's
nginx config, matching Student 4's pattern exactly (relative paths, proxy
to `127.0.0.1:<port>` for same-task calls), or (b) tell the team you want
your frontend to stay `external` with a public backend instead. Don't
guess this for yourself - it's a real design choice with security
implications, which is why it's `ingress: todo` in the manifest rather than
a guessed default.

## Team lead steps (one-time)

1. `cp config.env.example config.env` and fill in `AWS_REGION` (and
   `AWS_PROFILE` if you use named profiles).
2. Run `bash bootstrap.sh` with `GITHUB_ORG=<org>` and `GITHUB_REPO=<repo>`
   set - **read `bootstrap/oidc-role.yaml`'s own TODOs first**, they're not
   safe to deploy blindly.
3. Run the two `gh variable set` commands `bootstrap.sh` prints.
4. Run `bash env-setup.sh` once (safe to re-run later if anything changes).
5. Trigger `.github/workflows/cloud-deployment.yml` manually
   (`workflow_dispatch`) once at least Student 4's stack is ready - it
   already is.

## Student steps (filling in your own stack)

1. Open `deploy/services.yaml`, find your `TODO(owner: ...)` block.
2. Copy Student 4's entry structure exactly - three containers (database,
   backend, frontend), same keys.
3. Fill in: `build.dockerfile` (your real Dockerfile path), `container_port`
   (what your process listens on *inside* the container - not the
   `8001:80`-style host mapping from local `docker-compose.yml`), and `env`
   (your real env vars, with all four AI flags `"false"`).
4. For same-task calls (your backend → your own database): use
   `http://127.0.0.1:<port>`. For cross-stack calls (your backend → Student
   1's staff service): use the Service Connect name already in the
   manifest, e.g. `http://staff-backend:5001` - never a Docker Compose
   hostname like `student1-backend`, and never a task's IP.
5. Resolve the ingress decision noted above for your frontend.
6. Change `status: todo` to `status: ready`.
7. Run `DRY_RUN=true bash build-and-push-images.sh` and
   `DRY_RUN=true bash deploy.sh` yourself first - confirm your stack shows
   up correctly before asking the team lead to run a real deployment.

## Troubleshooting

- **`ServiceNotActiveException` on `update-service`.** The service was
  deleted (by `cleanup.sh`) and AWS still has an `INACTIVE` record of it.
  `grep -q ACTIVE` on that record's status text matches `INACTIVE` too
  (it's an unanchored substring match) - fixed here with `grep -qx ACTIVE`
  (exact match), but if you copy this pattern elsewhere, use `-x`.
- **`InvalidParameterException: Unable to assume the service linked role`.**
  A fresh AWS account doesn't have `AWSServiceRoleForECS` yet. `env-setup.sh`
  creates it automatically (`aws iam create-service-linked-role`,
  tolerating "already exists" on every later run).
- **The AWS CLI hangs with no output.** It opened a pager (`less`) and is
  waiting for a keypress that will never come in a script. `common.sh`
  exports `AWS_PAGER=""` unconditionally for exactly this reason.
- **502 Bad Gateway from an nginx-proxied frontend.** `proxy_pass` using an
  nginx *variable* (not a literal hostname) forces resolution through the
  `resolver` directive - it will not fall back to `/etc/hosts` for
  `localhost` the way a literal `proxy_pass` would. If that resolver is
  hardcoded to `127.0.0.11` (Docker Compose's embedded DNS), it has nothing
  to resolve against on Fargate and every proxied request 502s. Fix: read
  the real nameserver from `/etc/resolv.conf` at container startup (see
  `student-4Nicholas-Hatzidimitriou/frontend/docker-entrypoint.sh`'s
  `RESOLVER_IP` logic) instead of hardcoding either address.
- **Fargate quota / "RequestLimitExceeded".** New AWS accounts have low
  default Fargate vCPU quotas. If multiple stacks' tasks fail to start with
  a capacity error, check Service Quotas for "Fargate On-Demand vCPU
  resource count" in `ap-southeast-2` and request an increase.
- **Wrong AWS account.** Every script's `confirm_account` prints
  `Account: <id>, Region: <region>, Prefix: <prefix>` and requires typed
  confirmation before doing anything (skipped automatically in CI, or with
  `SKIP_CONFIRM=1`) - read that line before typing `yes`.

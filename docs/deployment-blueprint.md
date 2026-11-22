# Deployment blueprint

What was built after slice 7 so the API can run outside a laptop, and what's left before the first real deploy.

## What was built

| Piece | File | Why |
|---|---|---|
| Production image | `api/Dockerfile`, `api/.dockerignore` | Installs exactly what `uv.lock` pins, runs as a non-root user, keeps the database in `/data` |
| Startup | `api/docker-entrypoint.sh` | Runs `alembic upgrade head`, then replaces itself with uvicorn so the server receives the stop signal |
| Secret guard | `check_production` in `api/app/settings.py` | With `GARIMPO_ENV=production`, the API refuses to start on the public default secret or one under 32 bytes |
| Database setting | `GARIMPO_DATABASE_URL` in `api/app/db.py` | The container's database lives on a volume |
| Bedrock provider | `create_client` in `api/app/llm/claude.py` | `GARIMPO_ASSIST_PROVIDER=bedrock` runs the same review through AWS |
| CI | `docker` job in `.github/workflows/ci.yml` | Builds the image, checks the secret guard and calls `/health` |

**New dependency:** `anthropic[bedrock]` adds `boto3`, the AWS SDK. The base `anthropic` package can't sign requests with AWS credentials (SigV4), and nothing else in the stack can.

**Swift comparison:** `create_client` is a small factory returning the same interface for two backends, like injecting a different `URLSession` configuration behind one protocol. The review loop doesn't know which one it got.

## Run it locally

```bash
docker build -t garimpo-api api
docker run -p 8000:8000 -v garimpo-data:/data \
  -e GARIMPO_JWT_SECRET="$(openssl rand -hex 32)" garimpo-api
```

Keep the secret: a new one signs everyone out. Create the first invite in the running container:

```bash
docker exec <container> python -m app.cli create-invite
```

## Assist configuration

| Provider | Settings |
|---|---|
| Off | Nothing; the app behaves as the MVP |
| Claude API | `ANTHROPIC_API_KEY` |
| Amazon Bedrock | `GARIMPO_ASSIST_PROVIDER=bedrock`, `AWS_REGION`, and AWS credentials from the host's IAM role |

- The Bedrock model defaults to `anthropic.claude-sonnet-5-5`. Check that your AWS account has access to it in the Bedrock console.
- The IAM role needs `bedrock-mantle:CreateInference` on that model.
- `usage_from` logs Claude API list prices. Bedrock regional endpoints carry a 10% premium, so the logged cost is slightly low there.

## Limits to know

- **One server only.** SQLite on a volume allows a single writer and a single container. Scaling out needs Postgres first.
- **Backups aren't set up.** Losing the volume loses all data.
- **HTTPS is the host's job.** The container serves plain HTTP on port 8000; put it behind a load balancer or proxy.

## Not done yet

1. **Choose the AWS host.** For one container with a persistent volume, Lightsail or a small EC2 instance is the simplest fit.
2. **Run the first deploy** and point the app's API URL at it.
3. **Run the live eval** on the provider you choose.

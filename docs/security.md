# Security and Deployment

## Authentication

Register with `POST /api/auth/register` and log in with `POST /api/auth/login`. Both accept a `username` and a 12–128 character password. User records are stored in SQLite with salted PBKDF2-HMAC-SHA256 hashes. Login issues a signed HS256 JWT with a 30-minute default lifetime; configure `JWT_SECRET_KEY` and optionally `JWT_EXPIRY_MINUTES`.

The orchestrator process endpoint requires a bearer token. The token subject must match the request `user_id`. Missing, invalid, and expired tokens return `401`; a subject mismatch returns `403`.

## Input and Output Controls

Query text is limited to 1,000 characters; orchestrator identity, session, crop-context, and location fields are also bounded. Control sequences and control/format characters are removed from query and prompt context fields. Known prompt-injection instructions are rejected with `400`; the security log records the event without copying the submitted instruction. Generated answer text is checked for unsafe prompt instructions and secret-like strings before delivery. This is not a semantic off-topic classifier; see the T-33 audit report for the accepted residual limitation.

The orchestrator endpoint uses a per-user sliding-window limit configured by `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` (30 requests per 60 seconds by default). A limit response is `429 RATE_LIMIT_EXCEEDED` and includes `Retry-After`.

## Production HTTPS

Set `APP_ENV=production`. The application refuses to start without `JWT_SECRET_KEY` and redirects HTTP requests to HTTPS. Set `CORS_ALLOWED_ORIGINS` to a comma-separated list of trusted frontend origins. Terminate TLS at a trusted ingress or reverse proxy with a valid certificate, enable HTTP-to-HTTPS redirection there, and configure the ASGI server to accept forwarded scheme headers only from that trusted proxy. Do not expose the application port directly to the public internet.

Use a high-entropy signing key (for example, generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"`), store it in the deployment secret manager, and never commit it. Mount persistent storage for `AUTH_DATABASE_PATH` and restrict its filesystem permissions. The built-in rate limiter is process-local; deployments with multiple workers or replicas should put rate-limit state in a shared store before scaling out.

The local development configuration does not redirect HTTP, so local API calls may use `http://localhost`. Production traffic must enter through HTTPS only.
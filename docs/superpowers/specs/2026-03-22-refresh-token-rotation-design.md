# Refresh Token Rotation Design

## Problem

Refresh tokens are stateless JWTs with no server-side tracking. Once issued, a refresh token remains valid for its full 30-day lifetime regardless of whether it has been rotated or the user has logged out. A stolen refresh token can be used indefinitely until it expires.

## Solution

Implement server-side refresh token tracking with token family rotation and replay detection, following the model described in RFC 6819 and used by Auth0/Okta.

## Data Model

New `refresh_tokens` table:

| Column | Type | Notes |
|--------|------|-------|
| `id` | `INTEGER` PK | Auto-increment |
| `jti` | `VARCHAR(36)` UNIQUE, indexed | UUID stored in the JWT `jti` claim; the DB lookup key |
| `user_id` | `INTEGER` FK -> `users.id` | CASCADE delete |
| `family_id` | `VARCHAR(36)` indexed | Groups tokens from the same login session |
| `revoked_at` | `DATETIME(tz)` nullable | NULL = active; set on rotation or revocation |
| `expires_at` | `DATETIME(tz)` | Used for lazy cleanup |
| `created_at` | `DATETIME(tz)` | Server default `now()` (same pattern as other entities) |

Revoked tokens are retained as "tripwires" for replay detection until they naturally expire.

## Token Lifecycle

### Login

1. User authenticates with email/password (unchanged).
2. Use case generates a `family_id` (UUID4) and calls token service to create the token pair, passing `family_id`.
3. Token service generates access token + refresh token JWT. The refresh token includes a `jti` (UUID4) claim.
4. Token service returns a `TokenPairWithMetadata` containing the JWT strings plus `jti` and `family_id`.
5. Use case persists a `RefreshToken` entity to DB with `revoked_at = NULL`.
6. Refresh token set as httpOnly cookie (unchanged). Token pair returned to client (unchanged response shape).

### Registration

Same as login — `RegisterUserUseCase` also creates a token pair on successful registration and must persist a `RefreshToken` entity.

### Refresh

1. Client sends refresh token via cookie or body (unchanged).
2. Use case calls `token_service.verify_refresh_token(token)` which decodes the JWT (PyJWT validates the `exp` claim during decode — expired tokens are rejected here). Returns a `RefreshTokenClaims` dataclass with `user_id` and `jti`.
3. DB lookup by `jti`:
   - **Not found**: reject with `InvalidCredentialsError`.
   - **Found, `revoked_at` is set**: replay detected. Revoke all active tokens in the same `family_id` (only rows where `revoked_at IS NULL`). Raise `InvalidCredentialsError`.
   - **Found and active**: proceed.
4. Mark current token as revoked (`revoked_at = now`).
5. Use case calls token service to create new token pair with same `family_id`, new `jti`.
6. Persist new `RefreshToken` row to DB.
7. Lazy cleanup: delete expired tokens for this user (`expires_at < now`).
8. Return new token pair to client.

Note: the DB `expires_at` check (previously listed as a separate step) is redundant since PyJWT already validates `exp` at decode time. It remains useful for lazy cleanup queries only.

### Logout

1. Use case receives the refresh token string and calls `token_service.verify_refresh_token(token)` to extract the `jti` (delegating JWT decoding to the token service, not decoding directly).
2. Look up DB row by `jti`, revoke all active tokens in the same `family_id` (only rows where `revoked_at IS NULL`).
3. Clear cookie (unchanged).
4. If token is missing, invalid, or expired, logout still succeeds — just clears the cookie. No error thrown to the client.

### User Deletion

Handled automatically by `CASCADE` on the `user_id` FK.

## Replay Detection

Revoked tokens are kept in the DB until they naturally expire. When an attacker replays a previously-rotated token:

1. The token is found in the DB with `revoked_at` set.
2. All active tokens in the family are revoked, invalidating the legitimate user's current token.
3. Both attacker and legitimate user must re-authenticate.

This ensures a stolen-and-replayed token cannot coexist with a legitimate session.

### Concurrent Refresh Race Condition

If a client sends two concurrent refresh requests with the same token (e.g., multiple browser tabs, network retry), the second request will see the token as revoked and trigger family revocation. This is a known trade-off of the rotation model. No grace period is planned — this is the standard strict behavior used by Auth0/Okta. Clients should serialize their refresh calls.

## Architecture

### Domain Layer (`domain/identity/`)

- `entities/refresh_token.py`: `RefreshToken` entity extending `Entity[RefreshTokenId]`. Fields: `id`, `jti` (str), `user_id` (UserId), `family_id` (str), `revoked_at` (datetime | None), `expires_at` (datetime), `created_at` (datetime). Method: `revoke()` sets `revoked_at`.
- `RefreshTokenId` added to `domain/common/value_objects/ids.py`.

### Application Layer (`application/identity/`)

- **`protocols/refresh_token_repository.py`**: New protocol with methods:
  - `find_by_jti(jti: str) -> RefreshToken | None`
  - `save(token: RefreshToken) -> RefreshToken`
  - `revoke_family(family_id: str) -> None` — sets `revoked_at = now()` only on rows where `revoked_at IS NULL`
  - `delete_expired_for_user(user_id: UserId) -> None`

- **`protocols/token_service.py`**: Updated signatures:
  - `create_token_pair(user_id: int, family_id: str) -> TokenPairWithMetadata` — receives `family_id` from the use case (the use case owns family lifecycle). Returns a new `TokenPairWithMetadata` dataclass containing: `access_token`, `refresh_token`, `token_type`, `expires_in`, `jti`, `family_id`.
  - `verify_refresh_token(token: str) -> RefreshTokenClaims | None` — returns a `RefreshTokenClaims` dataclass with `user_id` (int) and `jti` (str), or `None` if invalid.

- **`TokenPairWithMetadata` and `RefreshTokenClaims`**: Defined in the application layer (e.g., `application/identity/dtos.py`) as plain dataclasses. This fixes the existing architectural violation where `TokenWithRefresh` (a Pydantic model in the infrastructure layer) was imported by application-layer use cases. The router will convert `TokenPairWithMetadata` to the existing `TokenWithRefresh` Pydantic response model.

- **`AuthenticateUserUseCase`**: Updated to generate `family_id`, call token service with it, persist `RefreshToken` to DB.
- **`RegisterUserUseCase`**: Same treatment — generate `family_id`, persist `RefreshToken`.
- **`RefreshAccessTokenUseCase`**: Updated with rotation logic (verify token, lookup by jti, replay detection, revoke old, create new with same family, lazy cleanup).

### Infrastructure Layer (`infrastructure/identity/`)

- **ORM model**: `RefreshTokenORM` added to `backend/src/models.py` (following existing convention — all ORM models live in this single file).
- **`mappers/refresh_token_mapper.py`**: `to_domain()` / `to_orm()` conversions.
- **`repositories/refresh_token_repository.py`**: Implements protocol using async SQLAlchemy.
- **`services/token_service.py`**: Updated to include `jti` (UUID4) claim in refresh token JWTs. `create_token_pair` receives `family_id` as parameter (use case generates it). `verify_refresh_token` returns `RefreshTokenClaims` with both `user_id` and `jti`. The adapter converts between the application-layer `TokenPairWithMetadata` type and the internal JWT operations.

### Router Layer

- No changes to endpoint signatures or response shapes.
- Routers convert `TokenPairWithMetadata` (from use cases) to `TokenWithRefresh` (Pydantic response model) — only the `access_token`, `refresh_token`, `token_type`, `expires_in` fields are exposed in the HTTP response. The `jti` and `family_id` are internal.
- `/logout` endpoint updated to call `LogoutUseCase` (via token service protocol for JWT decoding) before clearing the cookie.

### New Use Case

- `LogoutUseCase` in `application/identity/use_cases/authentication/`: Receives refresh token string, delegates to `token_service.verify_refresh_token()` for JWT decoding, then calls `refresh_token_repository.revoke_family()`. Fails silently if token is missing/invalid/expired.

### DI Container

- `SharedContainer`: Add `refresh_token_repository` factory.
- `IdentityContainer`: Wire `refresh_token_repository` into `AuthenticateUserUseCase`, `RefreshAccessTokenUseCase`, `RegisterUserUseCase`, and `LogoutUseCase`.

### Migration

- Next migration in sequence (number determined at implementation time): `create_refresh_tokens_table`.

## What Doesn't Change

- Access token verification: fully stateless, no DB lookup.
- `TokenWithRefresh` HTTP response shape: same fields returned to clients.
- Cookie settings: same httpOnly/secure/samesite config.
- Rate limiting: same limits.
- Plugin client flow (refresh token in body): still works. Note: plugin clients MUST update their stored refresh token from every refresh response, since the old one is immediately revoked.

## Testing Strategy

- **Domain unit tests**: `RefreshToken` entity creation, `revoke()` method, validation.
- **Use case unit tests** (mocked repository):
  - Login persists a refresh token.
  - Registration persists a refresh token.
  - Refresh with valid token rotates correctly.
  - Refresh with revoked token triggers family revocation.
  - Refresh with unknown `jti` raises error.
  - Lazy cleanup called during refresh.
  - Logout revokes family.
  - Logout with missing/invalid token succeeds silently.
- **Existing tests**: No API contract changes, so existing integration/e2e tests should continue to pass. The rotation is transparent to clients.

## Transaction Boundaries

Repositories handle their own commits (matching the existing project convention — all repositories call `db.commit()` internally). The `RefreshTokenRepository.save()` and `revoke_family()` methods commit within themselves. The refresh flow (revoke old, save new, cleanup) involves multiple sequential commits; this is acceptable because each step is independently valid:

- If the process fails after revoking the old token but before saving the new one, the user simply needs to re-login.
- Lazy cleanup deletion is best-effort and can fail without consequence.

The login and refresh routers do not need `DatabaseSession` dependencies or explicit `db.commit()` calls — the repository handles this internally, consistent with how all other repositories in the project work.

## Expired Token Cleanup

Lazy cleanup during refresh requests: delete tokens where `expires_at < now` for the current user. Per-user scope keeps the cleanup simple and avoids cross-user side effects. Tokens for inactive users accumulate but are harmless (they expire and are never looked up). No background task infrastructure needed.

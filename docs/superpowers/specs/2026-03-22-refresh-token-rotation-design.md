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
| `created_at` | `DATETIME(tz)` | Server default `now()` |

Revoked tokens are retained as "tripwires" for replay detection until they naturally expire.

## Token Lifecycle

### Login

1. User authenticates with email/password (unchanged).
2. Token service generates access token + refresh token JWT. The refresh token now includes a `jti` (UUID4) claim.
3. A `RefreshToken` entity is persisted to DB with a new `family_id` (UUID4) and `revoked_at = NULL`.
4. Refresh token set as httpOnly cookie (unchanged). Token pair returned to client (unchanged).

### Refresh

1. Client sends refresh token via cookie or body (unchanged).
2. JWT is decoded; `jti` extracted.
3. DB lookup by `jti`:
   - **Not found**: reject with `InvalidCredentialsError`.
   - **Found, `revoked_at` is set**: replay detected. Revoke all tokens in the same `family_id`. Raise `InvalidCredentialsError`.
   - **Found, `expires_at` < now**: reject (expired).
   - **Found and active**: proceed.
4. Mark current token as revoked (`revoked_at = now`).
5. Create new refresh token JWT with new `jti`, same `family_id`.
6. Persist new `RefreshToken` row to DB.
7. Lazy cleanup: delete expired tokens for this user (`expires_at < now`).
8. Return new token pair to client.

### Logout

1. Decode refresh token from cookie, extract `jti`.
2. Look up DB row, revoke all tokens in the same `family_id`.
3. Clear cookie (unchanged).
4. If token is missing or invalid, logout still succeeds (just clears the cookie).

### User Deletion

Handled automatically by `CASCADE` on the `user_id` FK.

## Replay Detection

Revoked tokens are kept in the DB until they naturally expire. When an attacker replays a previously-rotated token:

1. The token is found in the DB with `revoked_at` set.
2. The entire token family is revoked, invalidating the legitimate user's current token.
3. Both attacker and legitimate user must re-authenticate.

This ensures a stolen-and-replayed token cannot coexist with a legitimate session.

## Architecture

### Domain Layer (`domain/identity/`)

- `entities/refresh_token.py`: `RefreshToken` entity extending `Entity[RefreshTokenId]`. Fields: `id`, `jti` (str), `user_id` (UserId), `family_id` (str), `revoked_at` (datetime | None), `expires_at` (datetime), `created_at` (datetime). Method: `revoke()` sets `revoked_at`.
- `RefreshTokenId` added to `domain/common/value_objects/ids.py`.

### Application Layer (`application/identity/`)

- `protocols/refresh_token_repository.py`: New protocol with methods:
  - `find_by_jti(jti: str) -> RefreshToken | None`
  - `save(token: RefreshToken) -> RefreshToken`
  - `revoke_family(family_id: str) -> None`
  - `delete_expired_for_user(user_id: UserId) -> None`
- `protocols/token_service.py`: Updated to return structured data including `jti` and `family_id` so the use case can persist them.
- `AuthenticateUserUseCase`: Updated to persist refresh token to DB after authentication.
- `RefreshAccessTokenUseCase`: Updated with rotation logic (lookup by jti, replay detection, revoke old, create new, lazy cleanup).

### Infrastructure Layer (`infrastructure/identity/`)

- `models/refresh_token.py`: ORM model `RefreshTokenORM`.
- `mappers/refresh_token_mapper.py`: `to_domain()` / `to_orm()` conversions.
- `repositories/refresh_token_repository.py`: Implements protocol using async SQLAlchemy.
- `services/token_service.py`: Updated to include `jti` (UUID4) claim in refresh token JWTs. Returns structured data with `jti` and `family_id`.

### Router Layer

- No changes to endpoint signatures or response shapes.
- `/logout` endpoint updated to call a new `LogoutUseCase` before clearing the cookie.

### New Use Case

- `LogoutUseCase` in `application/identity/use_cases/authentication/`: Takes refresh token string, decodes `jti`, revokes the token family. Fails silently if token is missing/invalid.

### DI Container

- `SharedContainer`: Add `refresh_token_repository` factory.
- `IdentityContainer`: Wire `refresh_token_repository` into `AuthenticateUserUseCase`, `RefreshAccessTokenUseCase`, and `LogoutUseCase`.

### Migration

- `048_create_refresh_tokens_table.py`

## What Doesn't Change

- Access token verification: fully stateless, no DB lookup.
- `TokenWithRefresh` response shape: same fields.
- Cookie settings: same httpOnly/secure/samesite config.
- Rate limiting: same limits.
- Plugin client flow (refresh token in body): still works.

## Testing Strategy

- **Domain unit tests**: `RefreshToken` entity creation, `revoke()` method, validation.
- **Use case unit tests** (mocked repository):
  - Login persists a refresh token.
  - Refresh with valid token rotates correctly.
  - Refresh with revoked token triggers family revocation.
  - Refresh with unknown `jti` raises error.
  - Lazy cleanup called during refresh.
  - Logout revokes family.
- **Existing tests**: No API contract changes, so existing integration/e2e tests should continue to pass. The rotation is transparent to clients.

## Expired Token Cleanup

Lazy cleanup during refresh requests: delete tokens where `expires_at < now` for the current user. No background task infrastructure needed.

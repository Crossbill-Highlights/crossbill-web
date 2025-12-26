# Security Vulnerability Assessment Report

**Application:** Crossbill - KOReader Highlights Management System
**Assessment Date:** December 26, 2025
**Backend Framework:** FastAPI with SQLAlchemy
**Version Analyzed:** 0.2.1

---

## Executive Summary

This security assessment of the Crossbill backend codebase identifies several security vulnerabilities and areas for improvement across the OWASP Top 10 categories and general security best practices. The application demonstrates solid foundations in some areas (use of parameterized queries, modern password hashing) but has notable weaknesses in configuration security, file upload handling, and error information disclosure.

### Risk Summary

| Severity | Count |
|----------|-------|
| **Critical** | 1 |
| **High** | 4 |
| **Medium** | 6 |
| **Low** | 5 |
| **Informational** | 4 |

---

## Detailed Findings

### CRITICAL SEVERITY

#### 1. Insecure Default SECRET_KEY Configuration
**Location:** `backend/.env.example:10`, `backend/src/config.py:26`
**OWASP Category:** A02:2021 - Cryptographic Failures

**Finding:**
The `.env.example` file contains `SECRET_KEY=123`, which is a dangerously weak value. If this default is used in production, all JWT tokens become easily forgeable.

```python
# config.py:26
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
```

The empty string default in `config.py` provides no safety net, but the `.env.example` value `123` is equally problematic if copied without modification.

**Impact:** Complete authentication bypass - attackers can forge JWT tokens for any user.

**Recommendation:**
1. Add startup validation to fail if `SECRET_KEY` is empty, short, or matches known insecure values
2. Generate secure keys automatically on first run if not provided
3. Add minimum length requirement (32+ characters recommended)

```python
# Example validation
if len(settings.SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be at least 32 characters. Generate with: openssl rand -hex 32")
```

---

### HIGH SEVERITY

#### 2. Default Admin Credentials in Configuration
**Location:** `backend/src/config.py:44-45`
**OWASP Category:** A07:2021 - Identification and Authentication Failures

**Finding:**
```python
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin").strip()
```

Default credentials of `admin:admin` are set, and if `ADMIN_PASSWORD` environment variable is configured, the password is applied to the admin user on startup.

**Impact:** Predictable default credentials allow unauthorized administrative access.

**Recommendation:**
1. Remove default values for admin credentials
2. Require explicit configuration or fail startup
3. Enforce password complexity requirements

---

#### 3. Unrestricted File Upload Without Validation
**Location:** `backend/src/services/book_service.py:187-235`
**OWASP Category:** A04:2021 - Insecure Design

**Finding:**
The cover upload functionality accepts files without proper validation:

```python
def upload_cover(self, book_id: int, cover: UploadFile, user_id: int) -> schemas.CoverUploadResponse:
    # ...
    content = cover.file.read()  # No size limit
    cover_path.write_bytes(content)  # No content-type validation
```

**Issues Identified:**
1. **No file size limit** - Allows DoS through large file uploads
2. **No content-type validation** - Malicious files can be uploaded
3. **No magic byte verification** - Files with wrong extensions can be uploaded
4. **Overwrites without cleanup** - Old files are replaced without proper handling
5. **Fixed extension (.jpg)** - Forces all files to `.jpg` regardless of actual format

**Impact:**
- Denial of Service through resource exhaustion
- Potential for malicious file storage
- Storage of non-image files

**Recommendation:**
```python
import imghdr

MAX_COVER_SIZE = 5 * 1024 * 1024  # 5MB

def upload_cover(self, book_id: int, cover: UploadFile, user_id: int):
    # Check content-type header
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if cover.content_type not in allowed_types:
        raise HTTPException(400, "Only JPEG, PNG, and WebP images are allowed")

    # Read with size limit
    content = cover.file.read(MAX_COVER_SIZE + 1)
    if len(content) > MAX_COVER_SIZE:
        raise HTTPException(400, "File too large (max 5MB)")

    # Verify magic bytes
    file_type = imghdr.what(None, h=content)
    if file_type not in {"jpeg", "png", "webp"}:
        raise HTTPException(400, "Invalid image file")
```

---

#### 4. Overly Permissive CORS Configuration
**Location:** `backend/src/config.py:39-41`, `backend/src/main.py:146-152`
**OWASP Category:** A05:2021 - Security Misconfiguration

**Finding:**
```python
# config.py
CORS_ORIGINS: ClassVar[list[str]] = (
    os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") != "*" else ["*"]
)

# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials="*" not in settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The default CORS configuration allows all origins (`*`), which exposes the API to cross-origin attacks when deployed.

**Impact:** Cross-site request attacks from any origin when users are authenticated.

**Recommendation:**
1. Require explicit CORS origin configuration in production
2. Log a warning or fail startup if wildcard CORS is used in production environment
3. Document secure CORS configuration

---

#### 5. Verbose Error Messages Expose Internal Information
**Location:** Multiple routers (`users.py:35-39`, `books.py:48-52`, `highlights.py:50-54`)
**OWASP Category:** A01:2021 - Broken Access Control (Information Disclosure)

**Finding:**
Exception details are returned directly to clients:

```python
# users.py:35-39
except Exception as e:
    logger.error(f"Failed to register user: {e!s}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to register user: {e!s}",  # Exposes internal error
    ) from e
```

This pattern appears consistently across all routers.

**Impact:** Attackers gain insights into application internals, database structure, and error conditions that aid further attacks.

**Recommendation:**
Return generic error messages to clients while logging detailed errors internally:

```python
except Exception as e:
    logger.error(f"Failed to register user: {e!s}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred. Please try again later.",
    ) from e
```

---

### MEDIUM SEVERITY

#### 6. Missing Rate Limiting on Authentication Endpoints
**Location:** `backend/src/routers/auth.py`, `backend/src/routers/users.py`
**OWASP Category:** A07:2021 - Identification and Authentication Failures

**Finding:**
No rate limiting exists on login or registration endpoints, allowing:
- Brute force password attacks
- Credential stuffing attacks
- Account enumeration through timing attacks

**Impact:** Unauthorized access through automated attacks.

**Recommendation:**
Implement rate limiting using a library like `slowapi`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

---

#### 7. No Password Strength Validation
**Location:** `backend/src/schemas/user_schemas.py:21,29`
**OWASP Category:** A07:2021 - Identification and Authentication Failures

**Finding:**
Password validation only enforces minimum length:

```python
new_password: str | None = Field(None, min_length=8, description="New password (min 8 characters)")
password: str = Field(..., min_length=8, description="Password (min 8 characters)")
```

**Impact:** Users can set weak passwords like `password` or `12345678`.

**Recommendation:**
Add password complexity validation:

```python
from pydantic import field_validator
import re

class UserRegisterRequest(BaseModel):
    password: str = Field(..., min_length=8)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
```

---

#### 8. Missing Security Headers
**Location:** `backend/src/main.py`
**OWASP Category:** A05:2021 - Security Misconfiguration

**Finding:**
The application does not set security headers such as:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Strict-Transport-Security`
- `X-XSS-Protection`

**Impact:** Increased vulnerability to clickjacking, MIME-sniffing attacks, and XSS.

**Recommendation:**
Add a security headers middleware:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

---

#### 9. JWT Token Without Token Revocation
**Location:** `backend/src/services/auth_service.py`
**OWASP Category:** A07:2021 - Identification and Authentication Failures

**Finding:**
JWT tokens cannot be revoked before expiration. Once issued, a token remains valid until it expires.

**Impact:**
- Compromised tokens remain valid
- No logout functionality (client-side only)
- No ability to invalidate all sessions on password change

**Recommendation:**
Implement token revocation through:
1. Token blacklist (Redis or database)
2. Short-lived access tokens with refresh token rotation
3. Token versioning tied to user record

---

#### 10. Email Uniqueness Not Enforced at Database Level
**Location:** `backend/src/models.py:73`
**OWASP Category:** A04:2021 - Insecure Design

**Finding:**
```python
email: Mapped[str] = mapped_column(String(100), nullable=False)
# No unique constraint
```

Email uniqueness is only checked in application code, not at the database level.

**Impact:** Race conditions could allow duplicate email registrations.

**Recommendation:**
Add unique constraint to the User model:

```python
email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
```

---

#### 11. Potential Timing Attack in Password Verification
**Location:** `backend/src/services/auth_service.py:60-66`
**OWASP Category:** A07:2021 - Identification and Authentication Failures

**Finding:**
```python
def authenticate_user(email: str, password: str, db: DatabaseSession) -> User | None:
    user = _get_user_by_email(db, email)
    if not user:
        return None  # Early return - timing difference
    if not user.hashed_password or not _verify_password(password, user.hashed_password):
        return None
    return user
```

Early return when user doesn't exist creates a timing difference that could be used for user enumeration.

**Recommendation:**
Always perform password verification to equalize timing:

```python
def authenticate_user(email: str, password: str, db: DatabaseSession) -> User | None:
    user = _get_user_by_email(db, email)
    dummy_hash = hash_password("dummy_password")  # Pre-computed dummy

    if not user:
        _verify_password(password, dummy_hash)  # Constant time
        return None
    if not user.hashed_password or not _verify_password(password, user.hashed_password):
        return None
    return user
```

---

### LOW SEVERITY

#### 12. Logging of Sensitive Information
**Location:** `backend/src/repositories/user_repository.py:36-37,45-46`
**OWASP Category:** A09:2021 - Security Logging and Monitoring Failures

**Finding:**
```python
logger.info(f"Created user: {user.email} (id={user.id})")
logger.info(f"Created user with password: {user.email} (id={user.id})")
```

Email addresses are logged, which may be considered PII.

**Recommendation:** Consider logging user IDs only, or implement log sanitization.

---

#### 13. No Input Sanitization for HTML/XSS in Text Fields
**Location:** `backend/src/schemas/highlight_schemas.py:20`
**OWASP Category:** A03:2021 - Injection

**Finding:**
Highlight text and notes are stored without sanitization:

```python
text: str = Field(..., min_length=1, description="Highlighted text")
note: str | None = Field(None, description="Note/annotation")
```

While the frontend uses DOMPurify, relying solely on client-side sanitization is risky.

**Recommendation:** Implement server-side HTML sanitization for fields that may be rendered in HTML context.

---

#### 14. Static File Serving Security
**Location:** `backend/src/main.py:229-241`
**OWASP Category:** A01:2021 - Broken Access Control

**Finding:**
```python
@app.get("/{full_path:path}")
async def serve_spa(full_path: str) -> FileResponse:
    file_path = STATIC_DIR / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(STATIC_DIR / "index.html")
```

While basic path traversal is handled by FastAPI's routing, ensure `STATIC_DIR` resolution doesn't allow escape.

**Recommendation:** Add explicit path validation:

```python
file_path = (STATIC_DIR / full_path).resolve()
if not file_path.is_relative_to(STATIC_DIR):
    raise HTTPException(404, "Not found")
```

---

#### 15. No Request Body Size Limits
**Location:** `backend/src/main.py`
**OWASP Category:** A04:2021 - Insecure Design

**Finding:**
No global request body size limit is configured, potentially allowing large payloads that could cause DoS.

**Recommendation:**
Configure request body limits:

```python
from fastapi import Request

@app.middleware("http")
async def limit_request_body(request: Request, call_next):
    if request.headers.get("content-length"):
        if int(request.headers["content-length"]) > 10 * 1024 * 1024:  # 10MB
            return JSONResponse(status_code=413, content={"detail": "Request too large"})
    return await call_next(request)
```

---

#### 16. Insecure Cookie Settings (Frontend)
**Location:** `frontend/src/api/axios-instance.ts:12`
**OWASP Category:** A07:2021 - Identification and Authentication Failures

**Finding:**
```typescript
const AUTH_TOKEN_KEY = 'auth_token';
// Token stored in localStorage
localStorage.getItem(AUTH_TOKEN_KEY);
```

JWT tokens are stored in localStorage, which is accessible to JavaScript and vulnerable to XSS attacks.

**Recommendation:** Consider using httpOnly cookies for token storage with proper CSRF protection.

---

### INFORMATIONAL

#### 17. Development Database Credentials in Example File
**Location:** `backend/.env.example:3`

The example file contains development database credentials. While expected for examples, ensure documentation clearly states these must be changed.

#### 18. Missing HTTPS Enforcement
The application does not enforce HTTPS. In production, ensure HTTPS is enforced at the reverse proxy/load balancer level and add HSTS headers.

#### 19. No Account Lockout Policy
No mechanism exists to lock accounts after repeated failed login attempts.

#### 20. Missing Audit Logging
While request logging exists, there's no comprehensive audit trail for security-relevant actions (password changes, email changes, failed logins).

---

## Positive Security Observations

The codebase demonstrates several security best practices:

1. **Strong Password Hashing:** Uses Argon2 via `pwdlib.PasswordHash.recommended()` - industry-leading password hashing algorithm

2. **Parameterized Queries:** SQLAlchemy ORM consistently uses parameterized queries, preventing SQL injection

3. **User Isolation:** All database queries properly filter by `user_id`, preventing unauthorized data access

4. **Soft Delete Pattern:** Highlights use soft deletes, preserving audit trail

5. **Pydantic Validation:** Comprehensive input validation using Pydantic schemas

6. **Type Hints:** Extensive use of type hints enables static analysis tools

7. **Structured Logging:** Uses structlog for structured, parseable logging

8. **Request ID Tracking:** Each request gets a unique ID for tracing

---

## Recommendations Priority Matrix

| Priority | Finding | Effort |
|----------|---------|--------|
| **P0 - Immediate** | Insecure SECRET_KEY defaults | Low |
| **P0 - Immediate** | Default admin credentials | Low |
| **P1 - High** | File upload validation | Medium |
| **P1 - High** | Error message sanitization | Medium |
| **P2 - Medium** | Rate limiting implementation | Medium |
| **P2 - Medium** | Security headers | Low |
| **P2 - Medium** | CORS configuration | Low |
| **P3 - Low** | Password strength validation | Low |
| **P3 - Low** | Token revocation | High |
| **P4 - Consider** | Timing attack mitigation | Low |
| **P4 - Consider** | Email unique constraint | Low |

---

## Conclusion

The Crossbill backend demonstrates a solid security foundation with proper use of modern frameworks and patterns. However, several configuration and implementation weaknesses should be addressed before production deployment. The critical and high-severity findings should be prioritized for immediate remediation.

The most impactful improvements would be:
1. Secure secret key management with validation
2. Comprehensive file upload validation
3. Rate limiting on authentication endpoints
4. Generic error messages to prevent information leakage

---

*This report is based on static code analysis and does not include dynamic testing or penetration testing results.*

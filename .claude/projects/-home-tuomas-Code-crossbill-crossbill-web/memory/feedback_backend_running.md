---
name: Backend already running
description: The backend dev server is typically already running - don't try to start it. API generation can be done by the user.
type: feedback
---

Don't try to start the backend server - it's typically already running on port 8000.

**Why:** User runs the dev server themselves and it was already up.

**How to apply:** When needing to regenerate API types or check OpenAPI spec, assume the backend is running. Ask the user to run `npm run api:generate` if needed rather than trying to manage the server yourself.

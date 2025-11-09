# Frontend Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for setting up the Crossbill frontend application with modern React, TypeScript, and best practices.

**Tech Stack:**
- React 18+ (latest)
- TypeScript 5+ (latest)
- Vite (build tool)
- Material UI (component library)
- Tanstack Router (routing)
- Tanstack Query (data fetching/caching)
- Orval (API client generation)
- Luxon (date/time handling)
- Lodash (utility functions)
- ESLint + Prettier (code quality)
- Husky (git hooks)

---

## Phase 1: Project Initialization

### 1.1 Create Vite React TypeScript Project

```bash
cd frontend
npm create vite@latest . -- --template react-ts
```

**Configuration prompts:**
- Project name: `crossbill-frontend`
- Select framework: `React`
- Select variant: `TypeScript`

### 1.2 Install Core Dependencies

```bash
# Core dependencies
npm install @mui/material @emotion/react @emotion/styled
npm install @tanstack/react-router @tanstack/react-query
npm install luxon lodash

# Type definitions
npm install -D @types/luxon @types/lodash

# Development tools
npm install -D eslint prettier
npm install -D eslint-plugin-react eslint-plugin-react-hooks
npm install -D eslint-plugin-react-refresh @typescript-eslint/eslint-plugin @typescript-eslint/parser
npm install -D prettier-plugin-organize-imports
npm install -D husky lint-staged

# Orval for API generation
npm install -D orval
npm install axios # Orval peer dependency
```

### 1.3 Verify Installation

```bash
npm install
npm run dev
```

Navigate to `http://localhost:5173` to verify the default Vite app is running.

---

## Phase 2: Code Quality Setup

### 2.1 ESLint Configuration

Create `.eslintrc.cjs`:

```javascript
module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: [
    '@typescript-eslint',
    'react',
    'react-hooks',
    'react-refresh',
  ],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': [
      'error',
      { argsIgnorePattern: '^_' },
    ],
    'react/prop-types': 'off', // Using TypeScript for prop validation
    'no-console': ['warn', { allow: ['warn', 'error'] }],
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};
```

### 2.2 Prettier Configuration

Create `.prettierrc`:

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always",
  "endOfLine": "lf",
  "plugins": ["prettier-plugin-organize-imports"]
}
```

Create `.prettierignore`:

```
# Build outputs
dist
build
coverage

# Dependencies
node_modules

# Generated files
src/api/generated

# Config files
*.config.js
*.config.ts
vite.config.ts

# Lock files
package-lock.json
pnpm-lock.yaml
yarn.lock
```

### 2.3 Husky & Lint-Staged Setup

Initialize Husky:

```bash
npx husky init
```

Create `.husky/pre-commit`:

```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

npx lint-staged
```

Make it executable:

```bash
chmod +x .husky/pre-commit
```

Add to `package.json`:

```json
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,md,css}": [
      "prettier --write"
    ]
  }
}
```

---

## Phase 3: Material UI Setup

### 3.1 Create Theme Configuration

Create `src/theme/theme.ts`:

```typescript
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});
```

### 3.2 Update Main App

Update `src/main.tsx`:

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import App from './App';
import { theme } from './theme/theme';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
```

---

## Phase 4: Tanstack Router Setup

### 4.1 Install Additional Router Dependencies

```bash
npm install @tanstack/react-router-devtools
```

### 4.2 Create Router Configuration

Create `src/routes/__root.tsx`:

```typescript
import { Outlet, createRootRoute } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools';
import { Box } from '@mui/material';

export const Route = createRootRoute({
  component: () => (
    <Box>
      <Outlet />
      <TanStackRouterDevtools />
    </Box>
  ),
});
```

Create `src/routes/index.tsx`:

```typescript
import { createFileRoute } from '@tanstack/react-router';
import { Typography, Container } from '@mui/material';

export const Route = createFileRoute('/')({
  component: Index,
});

function Index() {
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom>
        Welcome to Crossbill
      </Typography>
      <Typography variant="body1">
        Your highlights management application
      </Typography>
    </Container>
  );
}
```

### 4.3 Update App Component

Update `src/App.tsx`:

```typescript
import { RouterProvider, createRouter } from '@tanstack/react-router';
import { routeTree } from './routeTree.gen';

const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

function App() {
  return <RouterProvider router={router} />;
}

export default App;
```

### 4.4 Generate Route Tree

Add to `package.json` scripts:

```json
{
  "scripts": {
    "routes:generate": "tsr generate"
  }
}
```

Create `tsr.config.json`:

```json
{
  "routesDirectory": "./src/routes",
  "generatedRouteTree": "./src/routeTree.gen.ts"
}
```

Run route generation:

```bash
npm run routes:generate
```

---

## Phase 5: Tanstack Query Setup

### 5.1 Create Query Client

Create `src/lib/queryClient.ts`:

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

### 5.2 Add Query Provider

Install devtools:

```bash
npm install @tanstack/react-query-devtools
```

Update `src/main.tsx`:

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import App from './App';
import { theme } from './theme/theme';
import { queryClient } from './lib/queryClient';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>
);
```

---

## Phase 6: Orval API Generation

### 6.1 Create Orval Configuration

Create `orval.config.ts`:

```typescript
import { defineConfig } from 'orval';

export default defineConfig({
  crossbill: {
    input: {
      target: 'http://localhost:8000/api/v1/openapi.json',
    },
    output: {
      mode: 'tags-split',
      target: './src/api/generated',
      schemas: './src/api/generated/model',
      client: 'react-query',
      httpClient: 'axios',
      mock: false,
      clean: true,
      prettier: true,
      override: {
        mutator: {
          path: './src/api/axios-instance.ts',
          name: 'axiosInstance',
        },
        query: {
          useQuery: true,
          useMutation: true,
          signal: true,
        },
      },
    },
  },
});
```

### 6.2 Create Axios Instance

Create `src/api/axios-instance.ts`:

```typescript
import Axios, { AxiosRequestConfig } from 'axios';

export const AXIOS_INSTANCE = Axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth tokens (future)
AXIOS_INSTANCE.interceptors.request.use(
  (config) => {
    // Future: Add auth token here
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
AXIOS_INSTANCE.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Future: Handle unauthorized
    }
    return Promise.reject(error);
  }
);

export const axiosInstance = <T>(
  config: AxiosRequestConfig
): Promise<T> => {
  const source = Axios.CancelToken.source();
  const promise = AXIOS_INSTANCE({
    ...config,
    cancelToken: source.token,
  }).then(({ data }) => data);

  // @ts-ignore
  promise.cancel = () => {
    source.cancel('Query was cancelled');
  };

  return promise;
};
```

### 6.3 Create Environment Variables

Create `.env`:

```env
VITE_API_URL=http://localhost:8000
```

Create `.env.example`:

```env
VITE_API_URL=http://localhost:8000
```

Add to `.gitignore`:

```
.env
.env.local
```

### 6.4 Add Generation Script

Add to `package.json`:

```json
{
  "scripts": {
    "api:generate": "orval",
    "dev": "npm run api:generate && vite",
    "build": "npm run api:generate && tsc && vite build"
  }
}
```

### 6.5 Generate API Client

**Before running, ensure backend server is running:**

```bash
# In backend directory
cd ../backend
poetry run uvicorn crossbill.main:app --reload
```

**Then generate API client:**

```bash
# In frontend directory
npm run api:generate
```

---

## Phase 7: Project Structure

Create the following directory structure:

```
frontend/
├── public/              # Static assets
├── src/
│   ├── api/
│   │   ├── generated/   # Auto-generated API client (gitignored)
│   │   └── axios-instance.ts
│   ├── components/      # Reusable components
│   │   ├── common/      # Common UI components
│   │   ├── layout/      # Layout components
│   │   └── features/    # Feature-specific components
│   ├── hooks/           # Custom React hooks
│   ├── lib/             # Utility libraries
│   │   └── queryClient.ts
│   ├── routes/          # Tanstack Router routes
│   │   ├── __root.tsx
│   │   └── index.tsx
│   ├── theme/           # MUI theme configuration
│   │   └── theme.ts
│   ├── types/           # TypeScript type definitions
│   ├── utils/           # Utility functions
│   │   ├── date.ts      # Luxon utilities
│   │   └── helpers.ts   # Lodash utilities
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── .eslintrc.cjs
├── .prettierrc
├── .prettierignore
├── .gitignore
├── .env
├── .env.example
├── orval.config.ts
├── tsr.config.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── package.json
└── claude.md            # Claude Code instructions
```

### Create Utility Helper Files

Create `src/utils/date.ts`:

```typescript
import { DateTime } from 'luxon';

/**
 * Format a date string to a readable format
 */
export const formatDate = (date: string | Date): string => {
  return DateTime.fromISO(date.toString()).toLocaleString(DateTime.DATE_MED);
};

/**
 * Format a date string to include time
 */
export const formatDateTime = (date: string | Date): string => {
  return DateTime.fromISO(date.toString()).toLocaleString(
    DateTime.DATETIME_MED
  );
};

/**
 * Get relative time (e.g., "2 hours ago")
 */
export const getRelativeTime = (date: string | Date): string => {
  return DateTime.fromISO(date.toString()).toRelative() || '';
};
```

Create `src/utils/helpers.ts`:

```typescript
import { debounce, memoize, isEmpty } from 'lodash';

/**
 * Debounced search handler
 */
export const createDebouncedSearch = <T extends (...args: any[]) => any>(
  fn: T,
  wait = 300
) => debounce(fn, wait);

/**
 * Memoized computation
 */
export const memoizeComputation = <T extends (...args: any[]) => any>(
  fn: T
) => memoize(fn);

/**
 * Check if value is empty (lodash)
 */
export { isEmpty };

/**
 * Safe array access
 */
export const safeArrayAccess = <T>(
  arr: T[] | undefined | null,
  index: number
): T | undefined => {
  return arr?.[index];
};
```

---

## Phase 8: Update Package.json Scripts

Update `package.json` with comprehensive scripts:

```json
{
  "scripts": {
    "dev": "npm run routes:generate && vite",
    "build": "npm run routes:generate && npm run api:generate && tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,json,css,md}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,json,css,md}\"",
    "type-check": "tsc --noEmit",
    "routes:generate": "tsr generate",
    "api:generate": "orval",
    "prepare": "husky install"
  }
}
```

---

## Phase 9: TypeScript Configuration

Update `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    /* Path aliases */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/utils/*": ["./src/utils/*"],
      "@/api/*": ["./src/api/*"],
      "@/types/*": ["./src/types/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

Update `vite.config.ts` to support path aliases:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/api': path.resolve(__dirname, './src/api'),
      '@/types': path.resolve(__dirname, './src/types'),
    },
  },
});
```

---

## Phase 10: Git Configuration

Update `.gitignore`:

```
# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Environment variables
.env
.env.local
.env.*.local

# Generated files
src/api/generated
src/routeTree.gen.ts

# Build outputs
coverage
```

---

## Implementation Checklist

### Phase 1: Project Initialization
- [ ] Create Vite React TypeScript project
- [ ] Install all core dependencies
- [ ] Verify initial setup runs

### Phase 2: Code Quality
- [ ] Configure ESLint
- [ ] Configure Prettier
- [ ] Set up Husky pre-commit hooks
- [ ] Configure lint-staged
- [ ] Test pre-commit hook runs linter and formatter

### Phase 3: Material UI
- [ ] Create theme configuration
- [ ] Update main.tsx with ThemeProvider
- [ ] Test Material UI components render

### Phase 4: Tanstack Router
- [ ] Install router dependencies
- [ ] Create root route
- [ ] Create index route
- [ ] Update App.tsx
- [ ] Configure and generate route tree
- [ ] Test routing works

### Phase 5: Tanstack Query
- [ ] Create query client configuration
- [ ] Add QueryClientProvider to main.tsx
- [ ] Install and configure devtools
- [ ] Test query setup

### Phase 6: Orval API Generation
- [ ] Create orval.config.ts
- [ ] Create axios instance
- [ ] Set up environment variables
- [ ] Ensure backend is running
- [ ] Generate API client
- [ ] Verify generated files

### Phase 7: Project Structure
- [ ] Create directory structure
- [ ] Create utility files (date.ts, helpers.ts)
- [ ] Organize existing files into structure

### Phase 8: Scripts & Configuration
- [ ] Update package.json scripts
- [ ] Update TypeScript configuration
- [ ] Update Vite configuration with path aliases
- [ ] Test all scripts work

### Phase 9: Final Verification
- [ ] Run `npm run lint`
- [ ] Run `npm run format`
- [ ] Run `npm run type-check`
- [ ] Run `npm run dev`
- [ ] Test pre-commit hook
- [ ] Create test commit to verify hooks

### Phase 10: Documentation
- [ ] Create claude.md with development rules
- [ ] Update README with setup instructions
- [ ] Document environment variables

---

## Post-Setup Development Workflow

### Daily Development

1. **Start development server:**
   ```bash
   npm run dev
   ```

2. **Before committing:**
   ```bash
   npm run lint:fix
   npm run format
   npm run type-check
   ```

3. **Regenerate API client when backend changes:**
   ```bash
   npm run api:generate
   ```

4. **Add new routes:**
   - Create new file in `src/routes/`
   - Run `npm run routes:generate`

### Pre-Commit Automation

Husky will automatically run:
1. ESLint with auto-fix
2. Prettier formatting

Only on staged files, ensuring commits are always clean.

---

## Next Steps After Setup

1. **Create Layout Components:**
   - AppBar with navigation
   - Sidebar (if needed)
   - Footer
   - Main layout wrapper

2. **Implement Core Features:**
   - Books list page
   - Highlights list page
   - Book details page
   - Highlight editor

3. **Add Authentication (future):**
   - Login page
   - Protected routes
   - Auth context
   - Token management

4. **Enhance UI:**
   - Loading states
   - Error boundaries
   - Toast notifications
   - Confirm dialogs

5. **Testing:**
   - Install Vitest
   - Add unit tests
   - Add integration tests

---

## Troubleshooting

### API Generation Fails

**Issue:** `npm run api:generate` fails

**Solutions:**
1. Ensure backend is running: `cd ../backend && poetry run uvicorn crossbill.main:app --reload`
2. Check `orval.config.ts` has correct backend URL
3. Verify backend OpenAPI endpoint: `http://localhost:8000/api/v1/openapi.json`

### Husky Hook Not Running

**Issue:** Pre-commit hook doesn't run

**Solutions:**
1. Reinstall Husky: `npm run prepare`
2. Check `.husky/pre-commit` is executable: `chmod +x .husky/pre-commit`
3. Verify git hooks path: `git config core.hooksPath`

### Import Path Aliases Not Working

**Issue:** TypeScript can't resolve `@/` imports

**Solutions:**
1. Verify `tsconfig.json` has paths configured
2. Verify `vite.config.ts` has aliases configured
3. Restart TypeScript server in your editor

### Material UI Styling Issues

**Issue:** MUI components don't have styles

**Solutions:**
1. Ensure `@emotion/react` and `@emotion/styled` are installed
2. Check ThemeProvider wraps App component
3. Verify CssBaseline is included

---

## Resources

- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Material UI Documentation](https://mui.com/)
- [Tanstack Router Documentation](https://tanstack.com/router)
- [Tanstack Query Documentation](https://tanstack.com/query)
- [Orval Documentation](https://orval.dev/)
- [Luxon Documentation](https://moment.github.io/luxon/)
- [Lodash Documentation](https://lodash.com/)

---

## Notes

- This setup prioritizes functional programming patterns as requested
- Lodash is available for functional utilities (map, filter, reduce, etc.)
- Luxon provides immutable date/time handling
- ESLint and Prettier run automatically on pre-commit via Husky
- API client regenerates automatically on build
- Path aliases make imports cleaner and more maintainable

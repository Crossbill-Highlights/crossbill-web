# Frontend Development Guidelines for Claude Code

## Code Quality Requirements

### Working style
- Always make logically separated commits when working on big changes

### Pre-Commit Checklist
- **ALWAYS** run linter before making commits: `npm run lint:fix`
- **ALWAYS** run formatter before making commits: `npm run format`
- Verify no TypeScript errors: `npm run type-check`
- Ensure all staged files pass quality checks

> Note: Husky pre-commit hooks will automatically run linter and formatter on staged files, but you should still manually verify before committing.

## Programming Style

### Functional Programming Principles
- **PREFER** functional programming style over imperative
- Use pure functions whenever possible (no side effects)
- Avoid mutations - prefer immutable data structures
- Use functional composition for complex logic

### Component Patterns
- **PREFER** functional components over class components
- Use hooks for state management and side effects
- Keep components small and focused (single responsibility)
- Extract reusable logic into custom hooks

### Lodash Usage
- **USE** lodash for functional utilities when necessary:
  - `map`, `filter`, `reduce` for array transformations
  - `groupBy`, `sortBy`, `uniqBy` for data manipulation
  - `debounce`, `throttle` for performance optimization
  - `memoize` for expensive computations
  - `isEmpty`, `isNil`, `has` for safe checks

### Examples

#### Good - Functional Style with Lodash
```typescript
import { map, filter, sortBy } from 'lodash';

// Pure function
const getActiveHighlights = (highlights: Highlight[]) => {
  return sortBy(
    filter(highlights, (h) => !h.archived),
    'created_at'
  );
};

// Functional component
const HighlightsList = ({ bookId }: Props) => {
  const { data: highlights } = useHighlights(bookId);

  const activeHighlights = useMemo(
    () => getActiveHighlights(highlights ?? []),
    [highlights]
  );

  return map(activeHighlights, (highlight) => (
    <HighlightCard key={highlight.id} highlight={highlight} />
  ));
};
```

#### Bad - Imperative Style
```typescript
// Avoid mutations and imperative loops
const HighlightsList = ({ bookId }: Props) => {
  const { data: highlights } = useHighlights(bookId);
  const [activeHighlights, setActiveHighlights] = useState([]);

  useEffect(() => {
    const active = [];
    for (let i = 0; i < highlights.length; i++) {
      if (!highlights[i].archived) {
        active.push(highlights[i]);
      }
    }
    active.sort((a, b) => a.created_at - b.created_at);
    setActiveHighlights(active);
  }, [highlights]);

  return activeHighlights.map(/* ... */);
};
```

## TypeScript Best Practices

- **ALWAYS** define explicit types for component props
- **PREFER** interfaces over types for object shapes
- **USE** type inference when obvious
- **AVOID** `any` - use `unknown` if type is truly unknown
- **USE** strict null checks - handle `undefined` and `null` explicitly

## State Management

- **USE** Tanstack Query for server state
- **USE** React hooks (useState, useReducer) for local component state
- **CONSIDER** Context API for shared UI state
- **AVOID** prop drilling - use composition or context

## API Integration

- **USE** generated API client from Orval
- **ALWAYS** handle loading and error states
- **USE** optimistic updates for better UX
- **INVALIDATE** queries after mutations

## Styling

- **USE** Material UI components when available
- **USE** MUI's `sx` prop for component-specific styles
- **USE** theme tokens for consistent spacing/colors
- **AVOID** inline styles except for dynamic values

## File Organization

- **GROUP** related components in feature folders
- **EXTRACT** reusable components to `components/common`
- **KEEP** route components in `routes/` folder
- **PLACE** business logic in separate utility files

## Performance

- **USE** `useMemo` for expensive computations
- **USE** `useCallback` for function props
- **USE** lodash `debounce` for search inputs
- **USE** `React.lazy` for code splitting
- **MEASURE** before optimizing

## Error Handling

- **ALWAYS** handle API errors gracefully
- **PROVIDE** user-friendly error messages
- **LOG** errors to console for debugging
- **USE** error boundaries for component failures

## Accessibility

- **USE** semantic HTML elements
- **PROVIDE** alt text for images
- **ENSURE** keyboard navigation works
- **USE** ARIA labels when necessary

## Code Comments

- **WRITE** comments for complex business logic
- **DOCUMENT** utility functions with JSDoc
- **EXPLAIN** non-obvious workarounds
- **AVOID** obvious comments

## Git Workflow

- **COMMIT** frequently with descriptive messages
- **RUN** `npm run lint:fix && npm run format` before committing
- **VERIFY** no console errors before pushing
- **KEEP** commits focused on single changes

## Testing (Future)

- Write unit tests for utilities
- Write integration tests for user flows
- Aim for high coverage of business logic
- Test error states and edge cases

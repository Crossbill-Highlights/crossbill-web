import { ReadingSessionsTab } from '@/pages/BookPage/ReadingSessionsTab/ReadingSessionsTab';
import { createFileRoute } from '@tanstack/react-router';

type SessionsSearch = {
  sessionPage?: number;
};

export const Route = createFileRoute('/book/$bookId/sessions')({
  component: ReadingSessionsTab,
  validateSearch: (search: Record<string, unknown>): SessionsSearch => ({
    sessionPage: search.sessionPage ? Number(search.sessionPage) : undefined,
  }),
});

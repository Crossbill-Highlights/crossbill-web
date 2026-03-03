import { ReadingSessionsPage } from '@/pages/BookPage/ReadingSessions/ReadingSessionsPage';
import { createFileRoute } from '@tanstack/react-router';

type SessionsSearch = {
  sessionPage?: number;
};

export const Route = createFileRoute('/book/$bookId/sessions')({
  component: ReadingSessionsPage,
  validateSearch: (search: Record<string, unknown>): SessionsSearch => ({
    sessionPage: search.sessionPage ? Number(search.sessionPage) : undefined,
  }),
});

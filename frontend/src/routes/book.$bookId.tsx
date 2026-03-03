import { BookPage } from '@/pages/BookPage/BookPage';
import { createFileRoute, redirect } from '@tanstack/react-router';

type RedirectRoute =
  | '/book/$bookId/highlights'
  | '/book/$bookId/flashcards'
  | '/book/$bookId/sessions'
  | '/book/$bookId/structure';

const tabRouteMap: Partial<Record<string, RedirectRoute>> = {
  highlights: '/book/$bookId/highlights',
  flashcards: '/book/$bookId/flashcards',
  readingSessions: '/book/$bookId/sessions',
  structure: '/book/$bookId/structure',
};

export const Route = createFileRoute('/book/$bookId')({
  component: BookPage,
  beforeLoad: ({ search, params }) => {
    // Redirect old tab-based URLs to new nested routes
    const tabParam = (search as Record<string, unknown>).tab as string | undefined;
    if (tabParam) {
      const route = tabRouteMap[tabParam] ?? '/book/$bookId/structure';
      throw redirect({
        to: route,
        params,
      });
    }
  },
});

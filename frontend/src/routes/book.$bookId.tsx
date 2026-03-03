import { BookPage } from '@/pages/BookPage/BookPage';
import { createFileRoute, redirect } from '@tanstack/react-router';

export const Route = createFileRoute('/book/$bookId')({
  component: BookPage,
  beforeLoad: ({ search, params }) => {
    // Redirect old tab-based URLs to new nested routes
    const tabParam = (search as Record<string, unknown>).tab as string | undefined;
    if (tabParam) {
      const tabRouteMap: Record<string, string> = {
        highlights: 'highlights',
        flashcards: 'flashcards',
        readingSessions: 'sessions',
        structure: 'structure',
      };
      const route = tabRouteMap[tabParam] || 'structure';
      throw redirect({
        to: `/book/$bookId/${route}`,
        params,
      });
    }
  },
});

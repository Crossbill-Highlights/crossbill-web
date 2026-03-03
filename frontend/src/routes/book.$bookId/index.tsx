import { createFileRoute, redirect } from '@tanstack/react-router';

export const Route = createFileRoute('/book/$bookId/')({
  beforeLoad: ({ params }) => {
    throw redirect({
      to: '/book/$bookId/structure',
      params,
    });
  },
});

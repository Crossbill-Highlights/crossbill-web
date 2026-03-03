import { BookPage } from '@/pages/BookPage/BookPage';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/book/$bookId')({
  component: BookPage,
});

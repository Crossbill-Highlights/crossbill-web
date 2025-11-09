import { createFileRoute } from '@tanstack/react-router';
import { BookPage } from '../components/BookPage/BookPage';

export const Route = createFileRoute('/book/$bookId')({
  component: BookPage,
});

import { ReflectionPage } from '@/pages/BookPage/Reflection/ReflectionPage';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/book/$bookId/reflection')({
  component: ReflectionPage,
});

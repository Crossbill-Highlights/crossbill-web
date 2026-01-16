import { LoginPage } from '@/pages/LoginPage/LoginPage';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/login')({
  component: LoginPage,
});

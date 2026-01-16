import { createFileRoute } from '@tanstack/react-router';
import { RegistrationPage } from '@/pages/RegistrationPage/RegistrationPage';

export const Route = createFileRoute('/register')({
  component: RegistrationPage,
});

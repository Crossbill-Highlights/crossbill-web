import { RegistrationPage } from '@/pages/RegistrationPage/RegistrationPage';
import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/register')({
  component: RegistrationPage,
});

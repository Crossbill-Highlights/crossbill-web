import { createFileRoute } from '@tanstack/react-router';
import { RegistrationPage } from '../components/RegistrationPage/RegistrationPage';

export const Route = createFileRoute('/register')({
  component: RegistrationPage,
});

import { createFileRoute } from '@tanstack/react-router';
import { LandingPage } from '../components/LandingPage/LandingPage';

type LandingPageSearch = {
  search?: string;
  page?: number;
};

export const Route = createFileRoute('/')({
  component: LandingPage,
  validateSearch: (search: Record<string, unknown>): LandingPageSearch => {
    return {
      search: (search?.search as string) || undefined,
      page: Number(search?.page) || 1,
    };
  },
});

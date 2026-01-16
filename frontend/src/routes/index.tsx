import { LandingPage } from '@/pages/LandingPage/LandingPage';
import { createFileRoute } from '@tanstack/react-router';

type LandingPageSearch = {
  search?: string;
  page?: number;
};

export const Route = createFileRoute('/')({
  component: LandingPage,
  validateSearch: (search: Record<string, unknown>): LandingPageSearch => {
    return {
      search: (search.search as string | undefined) || undefined,
      page: Number(search.page) || 1,
    };
  },
});

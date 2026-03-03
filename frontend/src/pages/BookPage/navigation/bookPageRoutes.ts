import {
  ChapterListIcon,
  FlashcardsIcon,
  HighlightsIcon,
  ReadingSessionIcon,
} from '@/theme/Icons.tsx';
import type { SvgIconComponent } from '@mui/icons-material';

export type BookPageRoute =
  | '/book/$bookId/structure'
  | '/book/$bookId/highlights'
  | '/book/$bookId/flashcards'
  | '/book/$bookId/sessions';

export interface BookPageRouteConfig {
  to: BookPageRoute;
  segment: string;
  label: string;
  icon: SvgIconComponent;
}

export const BOOK_PAGE_ROUTES: BookPageRouteConfig[] = [
  {
    to: '/book/$bookId/structure',
    segment: 'structure',
    label: 'Structure',
    icon: ChapterListIcon,
  },
  {
    to: '/book/$bookId/highlights',
    segment: 'highlights',
    label: 'Highlights',
    icon: HighlightsIcon,
  },
  {
    to: '/book/$bookId/flashcards',
    segment: 'flashcards',
    label: 'Flashcards',
    icon: FlashcardsIcon,
  },
  {
    to: '/book/$bookId/sessions',
    segment: 'sessions',
    label: 'Sessions',
    icon: ReadingSessionIcon,
  },
];

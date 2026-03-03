import type { BookDetails } from '@/api/generated/model';
import { createContext, useContext } from 'react';

interface BookPageContextValue {
  book: BookDetails;
  isDesktop: boolean;
  leftSidebarEl: HTMLDivElement | null;
  /** Whether a floating filter FAB is shown on mobile (affects ScrollToTop position) */
  hasFloatingFilter: boolean;
  setHasFloatingFilter: (visible: boolean) => void;
}

const BookPageContext = createContext<BookPageContextValue | null>(null);

export const BookPageProvider = BookPageContext.Provider;

export const useBookPage = (): BookPageContextValue => {
  const context = useContext(BookPageContext);
  if (!context) {
    throw new Error('useBookPage must be used within a BookPageProvider');
  }
  return context;
};

import type { Highlight } from '@/api/generated/model';
import { useGetNotesForBookApiV1BooksBookIdNotesGet } from '@/api/generated/notes/notes.ts';
import { Box, Tab, Tabs } from '@mui/material';
import { useState } from 'react';
import { HighlightFlashcardSection } from './HighlightFlashcardSection.tsx';
import { HighlightNotesSection } from './HighlightNotesSection.tsx';

const TAB_NOTES = 0;
const TAB_FLASHCARDS = 1;

const formatTabLabel = (label: string, count: number) =>
  count > 0 ? `${label} (${count})` : label;

interface HighlightTabsProps {
  highlight: Highlight;
  bookId: number;
  disabled?: boolean;
}

/**
 * Tabs for a highlight's secondary content: linked notes and flashcards —
 * mirroring the tabbed composition of `NoteViewModal` and `ChapterDetailDialog`.
 */
export const HighlightTabs = ({ highlight, bookId, disabled = false }: HighlightTabsProps) => {
  const [activeTab, setActiveTab] = useState(TAB_NOTES);

  const { data, isLoading } = useGetNotesForBookApiV1BooksBookIdNotesGet(bookId, {
    highlight_id: highlight.id,
  });
  // NOTE: the orval axios mutator unwraps the response (`.then(({ data }) => data)`),
  // so the generated GET hook's `data` is the payload itself, not an AxiosResponse.
  const notes = data?.notes ?? [];

  return (
    <Box>
      <Tabs
        value={activeTab}
        onChange={(_, newValue: number) => setActiveTab(newValue)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ borderBottom: 1, borderColor: 'divider' }}
        onTouchStart={(e) => e.stopPropagation()}
        onTouchMove={(e) => e.stopPropagation()}
        onTouchEnd={(e) => e.stopPropagation()}
      >
        <Tab label={formatTabLabel('Notes', notes.length)} />
        <Tab label={formatTabLabel('Flashcards', highlight.flashcards.length)} />
      </Tabs>
      <Box sx={{ pt: 2 }}>
        {activeTab === TAB_NOTES && (
          <HighlightNotesSection
            highlight={highlight}
            bookId={bookId}
            notes={notes}
            isLoading={isLoading}
            disabled={disabled}
          />
        )}
        {activeTab === TAB_FLASHCARDS && (
          <HighlightFlashcardSection highlight={highlight} bookId={bookId} disabled={disabled} />
        )}
      </Box>
    </Box>
  );
};

import type { Highlight, NoteLinkedChapter, NoteWithLinks } from '@/api/generated/model';
import { HighlightCard } from '@/pages/BookPage/Highlights/HighlightCard.tsx';
import { NoteFlashcardSection } from '@/pages/BookPage/Notes/components/NoteFlashcardSection.tsx';
import { Box, List, ListItemButton, ListItemText, Stack, Tab, Tabs } from '@mui/material';
import { type ReactElement, useState } from 'react';

interface NoteTabsProps {
  note: NoteWithLinks;
  bookId: number;
  highlights: Highlight[];
  chapters: NoteLinkedChapter[];
  onOpenHighlight: (highlightId: number) => void;
  onOpenChapter: (chapterId: number) => void;
  disabled?: boolean;
}

const formatTabLabel = (label: string, count: number) =>
  count > 0 ? `${label} (${count})` : label;

/**
 * Tabs for a note's secondary content: linked highlights, linked chapters and
 * the note's flashcards. The Highlights tab reuses the shared `HighlightCard`;
 * the Chapters tab lists clickable rows. Highlights/Chapters tabs render only
 * when non-empty, but the Flashcards tab is always present so a card can be
 * created — mirroring `ChapterDetailDialog`'s tabbed composition.
 */
export const NoteTabs = ({
  note,
  bookId,
  highlights,
  chapters,
  onOpenHighlight,
  onOpenChapter,
  disabled = false,
}: NoteTabsProps) => {
  const tabs = [
    highlights.length > 0 && {
      key: 'highlights',
      label: formatTabLabel('Highlights', highlights.length),
      content: (
        <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
          {highlights.map((highlight) => (
            <li key={highlight.id}>
              <HighlightCard highlight={highlight} onOpenModal={onOpenHighlight} />
            </li>
          ))}
        </Stack>
      ),
    },
    chapters.length > 0 && {
      key: 'chapters',
      label: formatTabLabel('Chapters', chapters.length),
      content: (
        <List disablePadding>
          {chapters.map((chapter) => (
            <ListItemButton key={chapter.id} onClick={() => onOpenChapter(chapter.id)}>
              <ListItemText primary={chapter.name} />
            </ListItemButton>
          ))}
        </List>
      ),
    },
    {
      key: 'flashcards',
      label: formatTabLabel('Flashcards', note.flashcards?.length ?? 0),
      content: <NoteFlashcardSection note={note} bookId={bookId} disabled={disabled} />,
    },
  ].filter((tab): tab is { key: string; label: string; content: ReactElement } => tab !== false);

  const [activeTab, setActiveTab] = useState(0);

  if (tabs.length === 0) return null;

  // Guard against the active index pointing past the available tabs.
  const safeActiveTab = Math.min(activeTab, tabs.length - 1);

  return (
    <Box>
      <Tabs
        value={safeActiveTab}
        onChange={(_, newValue: number) => setActiveTab(newValue)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ borderBottom: 1, borderColor: 'divider' }}
      >
        {tabs.map((tab) => (
          <Tab key={tab.key} label={tab.label} />
        ))}
      </Tabs>
      <Box sx={{ pt: 1 }}>{tabs[safeActiveTab]?.content}</Box>
    </Box>
  );
};

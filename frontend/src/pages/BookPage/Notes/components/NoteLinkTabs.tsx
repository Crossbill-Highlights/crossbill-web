import type { Highlight, NoteLinkedChapter } from '@/api/generated/model';
import { HighlightCard } from '@/pages/BookPage/Highlights/HighlightCard.tsx';
import { Box, List, ListItemButton, ListItemText, Stack, Tab, Tabs } from '@mui/material';
import { type ReactElement, useState } from 'react';

interface NoteLinkTabsProps {
  highlights: Highlight[];
  chapters: NoteLinkedChapter[];
  onOpenHighlight: (highlightId: number) => void;
  onOpenChapter: (chapterId: number) => void;
}

const formatTabLabel = (label: string, count: number) =>
  count > 0 ? `${label} (${count})` : label;

/**
 * Tabs listing a note's linked entities (highlights, chapters). The Highlights
 * tab reuses the shared `HighlightCard`; the Chapters tab lists clickable rows.
 * Only tabs whose entity type has items are rendered, mirroring
 * `ChapterDetailDialog`'s tabbed composition.
 */
export const NoteLinkTabs = ({
  highlights,
  chapters,
  onOpenHighlight,
  onOpenChapter,
}: NoteLinkTabsProps) => {
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

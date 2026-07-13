import type { NoteLinkedChapter, NoteLinkedHighlight } from '@/api/generated/model';
import { QuoteIcon } from '@/theme/Icons.tsx';
import { Box, List, ListItemButton, ListItemText, Tab, Tabs } from '@mui/material';
import { type ReactElement, useState } from 'react';

interface NoteLinkTabsProps {
  highlights: NoteLinkedHighlight[];
  chapters: NoteLinkedChapter[];
  onOpenHighlight: (highlightId: number) => void;
  onOpenChapter: (chapterId: number) => void;
}

const formatTabLabel = (label: string, count: number) =>
  count > 0 ? `${label} (${count})` : label;

const PREVIEW_WORD_COUNT = 30;

/**
 * Preview a highlight's text like `HighlightCard`: prepend `...` when it starts
 * mid-sentence (lowercase) and append `...` when truncated to the preview length.
 */
const formatHighlightPreview = (text: string) => {
  const startsWithLowercase =
    text.length > 0 && text[0] === text[0].toLowerCase() && text[0] !== text[0].toUpperCase();
  const withLeadingEllipsis = startsWithLowercase ? `...${text}` : text;

  const words = withLeadingEllipsis.split(/\s+/);
  return words.length > PREVIEW_WORD_COUNT
    ? words.slice(0, PREVIEW_WORD_COUNT).join(' ') + '...'
    : withLeadingEllipsis;
};

/**
 * Tabs listing a note's linked entities (highlights, chapters) as clickable
 * rows. Each row navigates to the target entity via its deep link. Only tabs
 * whose entity type has items are rendered, mirroring `ChapterDetailDialog`'s
 * tabbed composition.
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
        <List disablePadding>
          {highlights.map((highlight) => (
            <ListItemButton
              key={highlight.id}
              onClick={() => onOpenHighlight(highlight.id)}
              sx={{ alignItems: 'start', gap: 1.5 }}
            >
              <QuoteIcon
                sx={{ fontSize: 20, color: 'primary.main', flexShrink: 0, mt: 0.3, opacity: 0.7 }}
              />
              <ListItemText primary={formatHighlightPreview(highlight.text)} />
            </ListItemButton>
          ))}
        </List>
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

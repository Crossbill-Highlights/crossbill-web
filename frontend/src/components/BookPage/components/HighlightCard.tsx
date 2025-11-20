import { useGetHighlightTagsApiV1BookBookIdHighlightTagsGet } from '@/api/generated/books/books.ts';
import type { Bookmark, Highlight } from '@/api/generated/model';
import { TagList } from '@/components/BookPage/components/TagList.tsx';
import {
  Bookmark as BookmarkIcon,
  CalendarMonth as CalendarIcon,
  Notes as NotesIcon,
  FormatQuote as QuoteIcon,
} from '@mui/icons-material';
import { Box, Typography } from '@mui/material';
import { useState } from 'react';
import { HighlightViewModal } from './HighlightViewModal';

export interface HighlightCardProps {
  highlight: Highlight;
  bookId: number;
  bookmark?: Bookmark;
  allHighlights?: Highlight[];
  currentIndex?: number;
}

interface FooterProps {
  highlight: Highlight;
  bookmark?: Bookmark;
}

const Footer = ({ highlight, bookmark }: FooterProps) => {
  const hasBookmark = !!bookmark;

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', sm: 'row' },
        gap: 2,
        mt: 1,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          pl: 4.5,
          opacity: 0.6,
        }}
      >
        <CalendarIcon
          sx={(theme) => ({
            fontSize: 14,
            color:
              theme.palette.mode === 'light' ? `theme.palette.secondary.main` : 'secondary.light',
          })}
        />
        <Typography
          variant="caption"
          sx={(theme) => ({
            color:
              theme.palette.mode === 'light' ? `theme.palette.secondary.main` : 'secondary.light',
          })}
        >
          <span>
            {new Date(highlight.datetime).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </span>
          {highlight.page && <span>&nbsp;&nbsp;•&nbsp;&nbsp;Page {highlight.page}</span>}
          {hasBookmark && (
            <span>
              &nbsp;&nbsp;•
              <BookmarkIcon sx={{ fontSize: 16, verticalAlign: 'middle', ml: 1, mt: -0.5 }} />
            </span>
          )}
          {highlight.note && (
            <span>
              &nbsp;&nbsp;•
              <NotesIcon sx={{ fontSize: 16, verticalAlign: 'middle', ml: 1, mt: -0.5 }} />
            </span>
          )}
        </Typography>
      </Box>

      <Box>
        <TagList tags={highlight.highlight_tags} />
      </Box>
    </Box>
  );
};

const previewWordCount = 40;

export const HighlightCard = ({
  highlight,
  bookId,
  bookmark,
  allHighlights,
  currentIndex,
}: HighlightCardProps) => {
  const startsWithLowercase =
    highlight.text.length > 0 &&
    highlight.text[0] === highlight.text[0].toLowerCase() &&
    highlight.text[0] !== highlight.text[0].toUpperCase();
  const formattedText = startsWithLowercase ? `...${highlight.text}` : highlight.text;

  const words = formattedText.split(/\s+/);
  const shouldTruncate = words.length > previewWordCount;

  const previewText = shouldTruncate
    ? words.slice(0, previewWordCount).join(' ') + '...'
    : formattedText;

  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [currentHighlightIndex, setCurrentHighlightIndex] = useState(currentIndex ?? 0);

  // Fetch available tags for the book
  const { data: tagsResponse } = useGetHighlightTagsApiV1BookBookIdHighlightTagsGet(bookId);

  const handleOpenModal = () => {
    setCurrentHighlightIndex(currentIndex ?? 0);
    setViewModalOpen(true);
  };

  const handleNavigate = (newIndex: number) => {
    setCurrentHighlightIndex(newIndex);
  };

  const currentHighlight = allHighlights?.[currentHighlightIndex] ?? highlight;

  return (
    <>
      <Box
        id={`highlight-${highlight.id}`}
        onClick={handleOpenModal}
        sx={{
          position: 'relative',
          py: 3.5,
          px: 2.5,
          borderBottom: 1,
          borderColor: 'divider',
          borderLeft: 3,
          borderLeftStyle: 'solid',
          borderLeftColor: 'transparent',
          borderRadiusTopRight: 1.5,
          borderRadiusBottomRight: 1.5,
          transition: 'all 0.2s ease',
          cursor: 'pointer',
          '@media (hover: hover)': {
            '&:hover': {
              bgcolor: 'action.hover',
              borderLeftColor: 'primary.main',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
            },
          },
          '&:last-child': {
            borderBottom: 0,
          },
        }}
      >
        <Box sx={{ flex: 1, minWidth: 0 }}>
          {/* Quote Icon and Text */}
          <Box sx={{ display: 'flex', alignItems: 'start', gap: 1.5, mb: 2 }}>
            <QuoteIcon
              sx={{
                fontSize: 22,
                color: 'primary.main',
                flexShrink: 0,
                mt: 0.3,
                opacity: 0.7,
              }}
            />
            <Typography
              variant="body1"
              sx={{
                color: 'text.primary',
              }}
            >
              {previewText}
            </Typography>
          </Box>

          <Footer highlight={highlight} bookmark={bookmark} />
        </Box>
      </Box>

      {/* Highlight View Modal */}
      <HighlightViewModal
        highlight={currentHighlight}
        bookId={bookId}
        open={viewModalOpen}
        onClose={() => setViewModalOpen(false)}
        availableTags={tagsResponse?.tags || []}
        bookmark={bookmark}
        allHighlights={allHighlights}
        currentIndex={currentHighlightIndex}
        onNavigate={handleNavigate}
      />
    </>
  );
};

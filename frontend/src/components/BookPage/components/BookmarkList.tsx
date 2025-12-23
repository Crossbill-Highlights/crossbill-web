import type { Bookmark, Highlight } from '@/api/generated/model';
import { Bookmark as BookmarkIcon, ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import { Box, IconButton, Typography } from '@mui/material';
import { AnimatePresence, motion } from 'motion/react';
import { useState } from 'react';

interface BookmarkListProps {
  bookmarks: Bookmark[];
  allHighlights: Highlight[];
  onBookmarkClick: (highlightId: number) => void;
}

export const BookmarkList = ({ bookmarks, allHighlights, onBookmarkClick }: BookmarkListProps) => {
  const [isExpanded, setIsExpanded] = useState(true);

  // Create a map of highlight IDs to highlights for quick lookup
  const highlightMap = new Map(allHighlights.map((h) => [h.id, h]));

  // Get highlights for bookmarks and sort by page number
  const bookmarkedHighlights =
    bookmarks && bookmarks.length > 0
      ? bookmarks
          .map((bookmark) => ({
            bookmark,
            highlight: highlightMap.get(bookmark.highlight_id),
          }))
          .filter((item) => item.highlight !== undefined)
          .sort((a, b) => {
            const pageA = a.highlight?.page ?? Infinity;
            const pageB = b.highlight?.page ?? Infinity;
            return pageA - pageB;
          })
      : [];

  // Truncate highlight text to first few words
  const truncateText = (text: string, wordCount: number = 5): string => {
    const words = text.split(/\s+/);
    if (words.length <= wordCount) {
      return text;
    }
    return words.slice(0, wordCount).join(' ') + '...';
  };

  return (
    <Box
      sx={{
        flex: '1 1 auto',
        minHeight: 0,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 2,
          cursor: 'pointer',
          flexShrink: 0,
        }}
        onClick={() => setIsExpanded((prev) => !prev)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <BookmarkIcon sx={{ fontSize: 20, color: 'primary.main' }} />
          <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
            Bookmarks
          </Typography>
        </Box>
        <IconButton
          size="small"
          sx={{
            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s',
            display: { xs: 'none', lg: 'block' },
          }}
        >
          <ExpandMoreIcon fontSize="small" />
        </IconButton>
      </Box>

      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            style={{
              overflow: 'hidden',
              flex: '1 1 auto',
              minHeight: 0,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {bookmarkedHighlights.length > 0 ? (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 0.5,
                  flex: '1 1 auto',
                  minHeight: 0,
                }}
              >
                {bookmarkedHighlights.map(({ bookmark, highlight }) => {
                  if (!highlight) return null;

                  const startsWithLowercase =
                    highlight.text.length > 0 &&
                    highlight.text[0] === highlight.text[0].toLowerCase() &&
                    highlight.text[0] !== highlight.text[0].toUpperCase();

                  const prefix = startsWithLowercase ? '...' : '';
                  const truncatedText = prefix + truncateText(highlight.text);

                  return (
                    <Box
                      key={bookmark.id}
                      onClick={() => onBookmarkClick(highlight.id)}
                      sx={{
                        display: 'flex',
                        alignItems: 'start',
                        gap: 1,
                        py: 0.75,
                        px: 0.5,
                        borderRadius: 0.5,
                        cursor: 'pointer',
                        transition: 'background-color 0.2s ease',
                        '@media (hover: hover)': {
                          '&:hover': {
                            bgcolor: 'action.hover',
                          },
                        },
                      }}
                    >
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography
                          variant="body2"
                          sx={{
                            fontSize: '0.875rem',
                            color: 'text.primary',
                            lineHeight: 1.4,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {truncatedText}
                        </Typography>
                        {highlight.page && (
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ fontSize: '0.75rem', mt: 0.25, display: 'block' }}
                          >
                            Page {highlight.page}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  );
                })}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.813rem' }}>
                No bookmarks yet.
              </Typography>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
};

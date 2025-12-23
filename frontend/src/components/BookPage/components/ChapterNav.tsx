import { ExpandMore as ExpandMoreIcon, List as ListIcon } from '@mui/icons-material';
import { Box, IconButton, Typography } from '@mui/material';
import { AnimatePresence, motion } from 'motion/react';
import { useState } from 'react';
import type { ChapterData } from './ChapterList';

interface ChapterNavProps {
  chapters: ChapterData[];
  onChapterClick: (chapterId: number | string) => void;
}

export const ChapterNav = ({ chapters, onChapterClick }: ChapterNavProps) => {
  const [isExpanded, setIsExpanded] = useState(() => true);

  // If no chapters, don't render anything
  if (!chapters || chapters.length === 0) {
    return null;
  }

  return (
    <Box
      sx={{
        flex: '1 1 auto',
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
          <ListIcon sx={{ fontSize: 20, color: 'primary.main' }} />
          <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
            Chapters
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
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 0.5,
                flex: '1 1 auto',
                minHeight: 0,
              }}
            >
              {chapters.map((chapter) => (
                <Box
                  key={chapter.id}
                  onClick={() => onChapterClick(chapter.id)}
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
                      {chapter.name}
                    </Typography>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ fontSize: '0.75rem', mt: 0.25, display: 'block' }}
                    >
                      {chapter.highlights.length} highlight
                      {chapter.highlights.length !== 1 ? 's' : ''}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
};

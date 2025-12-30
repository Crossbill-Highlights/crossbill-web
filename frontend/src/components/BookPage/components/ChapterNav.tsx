import { Collapsable } from '@/components/common/animations/Collapsable.tsx';
import { ChapterListIcon, ExpandMoreIcon } from '@/components/common/Icons.tsx';
import { Box, IconButton, Typography } from '@mui/material';
import { useState } from 'react';

export interface ChapterNavigationData {
  id: number;
  name: string;
  itemCount: number;
}

interface ChapterNavProps {
  chapters: ChapterNavigationData[];
  onChapterClick: (chapterId: number) => void;
  hideTitle?: boolean;
}

export const ChapterNav = ({ chapters, onChapterClick, hideTitle }: ChapterNavProps) => {
  const [isExpanded, setIsExpanded] = useState(() => true);
  const effectiveIsExpanded = hideTitle ? true : isExpanded;

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
      {!hideTitle && (
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
            <ChapterListIcon sx={{ fontSize: 20, color: 'primary.main' }} />
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
      )}

      <Collapsable isExpanded={effectiveIsExpanded}>
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
                  {chapter.itemCount} highlight
                  {chapter.itemCount !== 1 ? 's' : ''}
                </Typography>
              </Box>
            </Box>
          ))}
        </Box>
      </Collapsable>
    </Box>
  );
};

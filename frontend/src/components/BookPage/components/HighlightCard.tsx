import type { Highlight } from '@/api/generated/model';
import {
  CalendarMonth as CalendarIcon,
  ChevronRight as ChevronRightIcon,
  FormatQuote as QuoteIcon,
} from '@mui/icons-material';
import { Box, CardContent, Collapse, IconButton, Typography } from '@mui/material';
import { useState } from 'react';
import { HoverableCard } from '../../common/HoverableCard';

export interface HighlightCardProps {
  highlight: Highlight;
}

const previewLength = 200;

export const HighlightCard = ({ highlight }: HighlightCardProps) => {
  const previewText =
    highlight.text.length > previewLength
      ? highlight.text.substring(0, previewLength) + '...'
      : highlight.text;

  const [isExpanded, setExpanded] = useState(false);
  const isExpandable = highlight.text.length > previewLength;

  return (
    <HoverableCard
      sx={{
        overflow: 'visible',
      }}
    >
      <CardContent
        onClick={() => (isExpandable ? setExpanded(!isExpanded) : null)}
        sx={{
          '&:last-child': { pb: 3 },
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'start',
            justifyContent: 'space-between',
            gap: 2,
          }}
        >
          <Box sx={{ flex: 1, minWidth: 0 }}>
            {/* Quote Icon and Text */}
            <Box sx={{ display: 'flex', alignItems: 'start', gap: 1.5, mb: 2 }}>
              <QuoteIcon
                sx={{
                  fontSize: 18,
                  color: 'primary.main',
                  flexShrink: 0,
                  mt: 0.3,
                }}
              />
              <Typography
                variant="body1"
                sx={{
                  fontWeight: 600,
                  color: 'text.primary',
                  lineHeight: 1.5,
                }}
              >
                {previewText}
              </Typography>
            </Box>

            <Collapse in={isExpanded}>
              <Typography
                variant="body1"
                sx={{
                  color: 'secondary.dark',
                  lineHeight: 1.6,
                  mb: 2,
                  pl: 4.5,
                }}
              >
                {highlight.text.length > previewLength && highlight.text.substring(previewLength)}
              </Typography>
            </Collapse>

            {/* Date and Page */}
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
                    theme.palette.mode === 'light'
                      ? `theme.palette.secondary.main`
                      : 'secondary.light',
                })}
              />
              <Typography
                variant="caption"
                sx={(theme) => ({
                  color:
                    theme.palette.mode === 'light'
                      ? `theme.palette.secondary.main`
                      : 'secondary.light',
                })}
              >
                {new Date(highlight.datetime).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
                {highlight.page && ` • Page ${highlight.page}`}
              </Typography>
            </Box>
          </Box>

          {isExpandable && (
            <IconButton
              size="small"
              sx={{
                color: 'primary.main',
                transition: 'transform 0.2s',
                transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                flexShrink: 0,
              }}
            >
              <ChevronRightIcon />
            </IconButton>
          )}
        </Box>
      </CardContent>
    </HoverableCard>
  );
};

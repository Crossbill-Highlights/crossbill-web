import {
  CalendarMonth as CalendarIcon,
  ChevronRight as ChevronRightIcon,
  FormatQuote as QuoteIcon,
} from '@mui/icons-material';
import { Box, CardContent, Collapse, IconButton, Typography } from '@mui/material';
import { HoverableCard } from '../../common/HoverableCard';

export interface Highlight {
  id: number;
  text: string;
  datetime: string;
  page?: number;
}

export interface HighlightCardProps {
  highlight: Highlight;
  isExpanded: boolean;
  onToggle: (id: number) => void;
}

export const HighlightCard = ({ highlight, isExpanded, onToggle }: HighlightCardProps) => {
  const previewText =
    highlight.text.length > 120 ? highlight.text.substring(0, 120) + '...' : highlight.text;

  return (
    <HoverableCard
      sx={{
        overflow: 'visible',
      }}
    >
      <CardContent
        onClick={() => onToggle(highlight.id)}
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

            {/* Expanded Full Text */}
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
                {highlight.text.length > 120 && highlight.text.substring(120)}
              </Typography>
            </Collapse>

            {/* Date and Page */}
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                pl: 4.5,
              }}
            >
              <CalendarIcon
                sx={(theme) => ({
                  fontSize: 14,
                  color:
                    theme.palette.mode === 'light'
                      ? `rgba(${parseInt(theme.palette.secondary.main.slice(1, 3), 16)}, ${parseInt(theme.palette.secondary.main.slice(3, 5), 16)}, ${parseInt(theme.palette.secondary.main.slice(5, 7), 16)}, 0.7)`
                      : 'secondary.light',
                })}
              />
              <Typography
                variant="caption"
                sx={(theme) => ({
                  color:
                    theme.palette.mode === 'light'
                      ? `rgba(${parseInt(theme.palette.secondary.main.slice(1, 3), 16)}, ${parseInt(theme.palette.secondary.main.slice(3, 5), 16)}, ${parseInt(theme.palette.secondary.main.slice(5, 7), 16)}, 0.9)`
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

          {/* Expand/Collapse Icon */}
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
        </Box>
      </CardContent>
    </HoverableCard>
  );
};

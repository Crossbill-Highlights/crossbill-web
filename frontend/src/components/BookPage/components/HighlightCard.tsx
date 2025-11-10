import type { Highlight } from '@/api/generated/model';
import {
  CalendarMonth as CalendarIcon,
  ChevronRight as ChevronRightIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  FormatQuote as QuoteIcon,
} from '@mui/icons-material';
import {
  Box,
  CardContent,
  Collapse,
  IconButton,
  ListItemIcon,
  Menu,
  MenuItem,
  Typography,
} from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useDeleteHighlightsApiV1BookBookIdHighlightDelete } from '../../../api/generated/books/books';
import { HoverableCard } from '../../common/HoverableCard';

export interface HighlightCardProps {
  highlight: Highlight;
  bookId: number;
}

const previewWordCount = 40;

export const HighlightCard = ({ highlight, bookId }: HighlightCardProps) => {
  const startsWithLowercase =
    highlight.text.length > 0 &&
    highlight.text[0] === highlight.text[0].toLowerCase() &&
    highlight.text[0] !== highlight.text[0].toUpperCase();
  const formattedText = startsWithLowercase ? `...${highlight.text}` : highlight.text;

  const words = formattedText.split(/\s+/);
  const isExpandable = words.length > previewWordCount;

  const previewText = isExpandable
    ? words.slice(0, previewWordCount).join(' ') + '...'
    : formattedText;

  const remainingText = isExpandable ? words.slice(previewWordCount).join(' ') : '';

  const [isExpanded, setExpanded] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const menuOpen = Boolean(anchorEl);
  const queryClient = useQueryClient();

  const deleteHighlightMutation = useDeleteHighlightsApiV1BookBookIdHighlightDelete();

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = (event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation();
    }
    setAnchorEl(null);
  };

  const handleDelete = async (event: React.MouseEvent) => {
    event.stopPropagation();
    handleMenuClose();

    if (
      confirm(
        'Are you sure you want to delete this highlight? This will soft-delete the highlight and prevent it from being recreated during sync.'
      )
    ) {
      try {
        await deleteHighlightMutation.mutateAsync({
          bookId,
          data: { highlight_ids: [highlight.id] },
        });
        // Invalidate and immediately refetch the book details query to refresh the UI
        await queryClient.invalidateQueries({
          queryKey: ['GetBookDetailsApiV1BookBookIdGet', bookId],
          refetchType: 'active',
        });
        await queryClient.refetchQueries({
          queryKey: ['GetBookDetailsApiV1BookBookIdGet', bookId],
        });
      } catch (error) {
        console.error('Failed to delete highlight:', error);
        alert('Failed to delete highlight. Please try again.');
      }
    }
  };

  return (
    <HoverableCard
      sx={{
        overflow: 'visible',
        position: 'relative',
      }}
    >
      {/* Menu Button */}
      <IconButton
        size="small"
        onClick={handleMenuOpen}
        sx={{
          position: 'absolute',
          bottom: 18,
          right: 18,
          zIndex: 1,
          '&:hover': {
            bgcolor: 'background.paper',
          },
        }}
      >
        <MoreVertIcon fontSize="small" />
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={menuOpen}
        onClose={(event) => handleMenuClose(event as React.MouseEvent)}
        onClick={(event) => event.stopPropagation()}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
      >
        <MenuItem onClick={handleDelete}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          Delete
        </MenuItem>
      </Menu>

      <CardContent
        onClick={() => (isExpandable ? setExpanded(!isExpanded) : null)}
        sx={{
          '&:last-child': { pb: 3 },
          pr: 2, // Make room for the menu button
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
                {remainingText}
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

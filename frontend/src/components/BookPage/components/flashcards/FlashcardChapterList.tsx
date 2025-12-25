import { getGetBookDetailsApiV1BooksBookIdGetQueryKey } from '@/api/generated/books/books';
import { useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete } from '@/api/generated/flashcards/flashcards';
import type { Flashcard } from '@/api/generated/model';
import { Collapsable } from '@/components/common/animations/Collapsable';
import { FadeInOut } from '@/components/common/animations/FadeInOut';
import { SectionTitle } from '@/components/common/SectionTitle';
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  FormatQuote as QuoteIcon,
  Visibility as RevealIcon,
  VisibilityOff as HideIcon,
} from '@mui/icons-material';
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  IconButton,
  Tooltip,
  Typography,
} from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

export interface FlashcardWithContext extends Flashcard {
  highlightText?: string;
  chapterName?: string;
  chapterId?: number;
  highlightTags?: { id: number; name: string }[];
}

export interface FlashcardChapterData {
  id: number | string;
  name: string;
  flashcards: FlashcardWithContext[];
}

interface FlashcardChapterListProps {
  chapters: FlashcardChapterData[];
  bookId: number;
  isLoading?: boolean;
  emptyMessage?: string;
  animationKey?: string;
  onEditFlashcard: (flashcard: FlashcardWithContext) => void;
}

export const FlashcardChapterList = ({
  chapters,
  bookId,
  isLoading,
  emptyMessage = 'No flashcards found.',
  animationKey = 'flashcard-chapters',
  onEditFlashcard,
}: FlashcardChapterListProps) => {
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          Searching...
        </Typography>
      </Box>
    );
  }

  return (
    <FadeInOut ekey={animationKey}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {chapters.length === 0 ? (
          <Typography variant="body1" color="text.secondary">
            {emptyMessage}
          </Typography>
        ) : (
          chapters.map((chapter) => (
            <Box key={chapter.id} id={`chapter-${chapter.id}`}>
              <SectionTitle showDivider>{chapter.name}</SectionTitle>

              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: '1fr',
                    sm: 'repeat(2, 1fr)',
                  },
                  gap: 2,
                }}
              >
                {chapter.flashcards.map((flashcard) => (
                  <FlashcardCard
                    key={flashcard.id}
                    flashcard={flashcard}
                    bookId={bookId}
                    onEdit={() => onEditFlashcard(flashcard)}
                  />
                ))}
              </Box>
            </Box>
          ))
        )}
      </Box>
    </FadeInOut>
  );
};

interface FlashcardCardProps {
  flashcard: FlashcardWithContext;
  bookId: number;
  onEdit: () => void;
}

const FlashcardCard = ({ flashcard, bookId, onEdit }: FlashcardCardProps) => {
  const [isRevealed, setIsRevealed] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const queryClient = useQueryClient();

  const deleteMutation = useDeleteFlashcardApiV1FlashcardsFlashcardIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
      },
      onError: (error) => {
        console.error('Failed to delete flashcard:', error);
        alert('Failed to delete flashcard. Please try again.');
      },
    },
  });

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this flashcard?')) return;

    setIsDeleting(true);
    try {
      await deleteMutation.mutateAsync({ flashcardId: flashcard.id });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit();
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        transition: 'all 0.2s ease',
        bgcolor: 'background.paper',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 3,
        },
        borderTop: '4px solid',
        borderTopColor: 'primary.main',
      }}
    >
      {/* Action buttons */}
      <Box
        sx={{
          position: 'absolute',
          top: 8,
          right: 8,
          display: 'flex',
          gap: 0.5,
          zIndex: 1,
          opacity: 0.7,
          transition: 'opacity 0.2s ease',
          '&:hover': {
            opacity: 1,
          },
        }}
      >
        <Tooltip title="Edit">
          <IconButton size="small" onClick={handleEdit} disabled={isDeleting}>
            <EditIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Delete">
          <IconButton
            size="small"
            onClick={handleDelete}
            disabled={isDeleting}
            sx={{ '&:hover': { color: 'error.main' } }}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      <CardActionArea
        onClick={() => setIsRevealed(!isRevealed)}
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'stretch',
          justifyContent: 'flex-start',
        }}
      >
        <CardContent sx={{ width: '100%', pt: 3 }}>
          {/* Question */}
          <Box sx={{ mb: 2, pr: 6 }}>
            <Typography
              variant="caption"
              sx={{
                color: 'primary.main',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                display: 'block',
                mb: 0.5,
              }}
            >
              Question
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 500, lineHeight: 1.5 }}>
              {flashcard.question}
            </Typography>
          </Box>

          {/* Answer Section */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
              <Typography
                variant="caption"
                sx={{
                  color: 'secondary.main',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Answer
              </Typography>
              {isRevealed ? (
                <HideIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
              ) : (
                <RevealIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
              )}
            </Box>

            {!isRevealed ? (
              <Box
                sx={{
                  py: 2,
                  px: 2,
                  bgcolor: 'action.hover',
                  borderRadius: 1,
                  textAlign: 'center',
                }}
              >
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  Click to reveal answer
                </Typography>
              </Box>
            ) : (
              <Collapsable isExpanded={isRevealed}>
                <Typography variant="body1" sx={{ color: 'text.secondary', lineHeight: 1.5 }}>
                  {flashcard.answer}
                </Typography>
              </Collapsable>
            )}
          </Box>

          {/* Source highlight preview */}
          {flashcard.highlightText && (
            <Collapsable isExpanded={isRevealed}>
              <Box
                sx={{
                  mt: 2,
                  pt: 2,
                  borderTop: '1px dashed',
                  borderColor: 'divider',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5 }}>
                  <QuoteIcon
                    sx={{ fontSize: 14, color: 'text.disabled', mt: 0.25, flexShrink: 0 }}
                  />
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'text.disabled',
                      fontStyle: 'italic',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      lineHeight: 1.4,
                    }}
                  >
                    {flashcard.highlightText}
                  </Typography>
                </Box>
              </Box>
            </Collapsable>
          )}
        </CardContent>
      </CardActionArea>
    </Card>
  );
};

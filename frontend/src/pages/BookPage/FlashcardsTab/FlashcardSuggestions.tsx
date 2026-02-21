import type { FlashcardSuggestionItem } from '@/api/generated/model';
import { FlashcardSuggestionCard } from '@/pages/BookPage/FlashcardsTab/FlashcardSuggestionCard.tsx';
import { AIIcon } from '@/theme/Icons.tsx';
import { Box, Button, CircularProgress, Stack, Typography } from '@mui/material';

interface FlashcardSuggestionsProps {
  suggestions: FlashcardSuggestionItem[];
  isLoading: boolean;
  disabled: boolean;
  onFetchSuggestions: () => void;
  onAcceptSuggestion: (suggestion: FlashcardSuggestionItem, index: number) => void;
  onRejectSuggestion: (index: number) => void;
}

export const FlashcardSuggestions = ({
  suggestions,
  isLoading,
  disabled,
  onFetchSuggestions,
  onAcceptSuggestion,
  onRejectSuggestion,
}: FlashcardSuggestionsProps) => {
  return (
    <>
      {suggestions.length ? (
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Suggested flashcards
        </Typography>
      ) : (
        <Button
          variant="text"
          size="small"
          startIcon={<AIIcon />}
          onClick={onFetchSuggestions}
          disabled={disabled || isLoading}
          sx={{ mb: 1 }}
        >
          Suggest flashcards
        </Button>
      )}

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )}

      {!isLoading && suggestions.length > 0 && (
        <Stack
          component="ul"
          sx={{
            gap: 2,
            listStyle: 'none',
            p: 0,
            m: 0,
            mb: 2,
          }}
        >
          {suggestions.map((suggestion, index) => (
            <li key={index}>
              <FlashcardSuggestionCard
                question={suggestion.question}
                answer={suggestion.answer}
                onAccept={() => onAcceptSuggestion(suggestion, index)}
                onReject={() => onRejectSuggestion(index)}
              />
            </li>
          ))}
        </Stack>
      )}
    </>
  );
};

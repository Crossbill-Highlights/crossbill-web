import type { FlashcardSuggestionItem } from '@/api/generated/model';
import { CardList } from '@/components/CardList.tsx';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { CreateFlashcardForm } from '@/pages/BookPage/Flashcards/CreateFlashcardForm.tsx';
import type { FlashcardWithContext } from '@/pages/BookPage/Flashcards/FlashcardChapterList.tsx';
import { FlashcardListCard } from '@/pages/BookPage/Flashcards/FlashcardListCard.tsx';
import { FlashcardSuggestions } from '@/pages/BookPage/Flashcards/FlashcardSuggestions.tsx';
import { Box, Typography } from '@mui/material';
import type { QueryKey } from '@tanstack/react-query';
import { useState } from 'react';

/**
 * Source-agnostic flashcard section for entity view modals (highlights, notes).
 * Renders the existing cards, a manual create/edit form and AI suggestions;
 * the caller wires the source-specific data and mutations.
 */
interface FlashcardSectionProps {
  /** Existing cards, pre-mapped and pre-sorted by the caller. */
  flashcards: FlashcardWithContext[];
  bookId: number;
  disabled?: boolean;
  isProcessing: boolean;
  /** Creates a card; resolves true on success (form is cleared only then). */
  onSaveFlashcard: (question: string, answer: string) => Promise<boolean>;
  /** Updates a card; resolves true on success. */
  onUpdateFlashcard: (flashcardId: number, question: string, answer: string) => Promise<boolean>;
  suggestions: FlashcardSuggestionItem[];
  suggestionsLoading: boolean;
  onFetchSuggestions: () => Promise<void>;
  onRemoveSuggestion: (index: number) => void;
  /** Query keys to invalidate when a card is deleted, in addition to book details. */
  additionalInvalidateKeys?: QueryKey[];
}

interface FlashcardsListProps {
  flashcardsWithContext: FlashcardWithContext[];
  bookId: number;
  onEdit: (flashcardId: number) => void;
  additionalInvalidateKeys?: QueryKey[];
}

const FlashcardsList = ({
  flashcardsWithContext,
  bookId,
  onEdit,
  additionalInvalidateKeys,
}: FlashcardsListProps) => {
  if (flashcardsWithContext.length === 0) {
    return null;
  }

  return (
    <CardList sx={{ mb: 2 }}>
      {flashcardsWithContext.map((flashcard) => (
        <li key={flashcard.id}>
          <FlashcardListCard
            flashcard={flashcard}
            bookId={bookId}
            onEdit={() => onEdit(flashcard.id)}
            showSourceHighlight={false}
            additionalInvalidateKeys={additionalInvalidateKeys}
          />
        </li>
      ))}
    </CardList>
  );
};

export const FlashcardSection = ({
  flashcards,
  bookId,
  disabled = false,
  isProcessing,
  onSaveFlashcard,
  onUpdateFlashcard,
  suggestions,
  suggestionsLoading,
  onFetchSuggestions,
  onRemoveSuggestion,
  additionalInvalidateKeys,
}: FlashcardSectionProps) => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [editingFlashcardId, setEditingFlashcardId] = useState<number | null>(null);

  const handleEditFlashcard = (flashcardId: number) => {
    const flashcard = flashcards.find((f) => f.id === flashcardId);
    if (flashcard) {
      setEditingFlashcardId(flashcardId);
      setQuestion(flashcard.question);
      setAnswer(flashcard.answer);
    }
  };

  const handleSave = async () => {
    const saved = editingFlashcardId
      ? await onUpdateFlashcard(editingFlashcardId, question, answer)
      : await onSaveFlashcard(question, answer);
    if (!saved) return;
    setQuestion('');
    setAnswer('');
    setEditingFlashcardId(null);
  };

  const handleCancelEdit = () => {
    setQuestion('');
    setAnswer('');
    setEditingFlashcardId(null);
  };

  const handleAcceptSuggestion = async (suggestion: FlashcardSuggestionItem, index: number) => {
    const saved = await onSaveFlashcard(suggestion.question, suggestion.answer);
    if (saved) {
      onRemoveSuggestion(index);
    }
  };

  return (
    <Box>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        Flashcards
      </Typography>

      <FlashcardsList
        flashcardsWithContext={flashcards}
        bookId={bookId}
        onEdit={handleEditFlashcard}
        additionalInvalidateKeys={additionalInvalidateKeys}
      />

      <CreateFlashcardForm
        question={question}
        answer={answer}
        onQuestionChange={setQuestion}
        onAnswerChange={setAnswer}
        editingFlashcardId={editingFlashcardId}
        isDisabled={disabled || isProcessing}
        isProcessing={isProcessing}
        onSave={handleSave}
        onCancelEdit={handleCancelEdit}
      />

      <AIFeature>
        <FlashcardSuggestions
          suggestions={suggestions}
          isLoading={suggestionsLoading}
          disabled={disabled}
          onFetchSuggestions={() => void onFetchSuggestions()}
          onAcceptSuggestion={(suggestion, index) => void handleAcceptSuggestion(suggestion, index)}
          onRejectSuggestion={onRemoveSuggestion}
        />
      </AIFeature>
    </Box>
  );
};

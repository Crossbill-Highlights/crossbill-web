import { Box, Button, TextField } from '@mui/material';

interface CreateFlashcardFormProps {
  question: string;
  answer: string;
  onQuestionChange: (value: string) => void;
  onAnswerChange: (value: string) => void;
  editingFlashcardId: number | null;
  isDisabled: boolean;
  isProcessing: boolean;
  onSave: () => void;
  onCancelEdit: () => void;
}

export const CreateFlashcardForm = ({
  question,
  answer,
  onQuestionChange,
  onAnswerChange,
  editingFlashcardId,
  isDisabled,
  isProcessing,
  onSave,
  onCancelEdit,
}: CreateFlashcardFormProps) => {
  const canSave = question.trim() && answer.trim() && !isDisabled;

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        alignItems: 'flex-start',
      }}
    >
      <TextField
        fullWidth
        size="small"
        value={question}
        onChange={(e) => onQuestionChange(e.target.value)}
        placeholder="Question..."
        disabled={isDisabled}
      />
      <TextField
        fullWidth
        size="small"
        multiline
        minRows={2}
        maxRows={4}
        value={answer}
        onChange={(e) => onAnswerChange(e.target.value)}
        placeholder="Answer..."
        disabled={isDisabled}
      />
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, width: '100%' }}>
        {editingFlashcardId && (
          <Button
            variant="text"
            size="small"
            onClick={onCancelEdit}
            disabled={isDisabled}
            sx={{ flexShrink: 0, height: 'fit-content', mt: 0.5 }}
          >
            Cancel
          </Button>
        )}
        <Button
          variant="text"
          size="small"
          onClick={onSave}
          disabled={!canSave}
          sx={{ flexShrink: 0, height: 'fit-content', mt: 0.5 }}
        >
          {isProcessing ? 'Saving...' : editingFlashcardId ? 'Update Flashcard' : 'Add Flashcard'}
        </Button>
      </Box>
    </Box>
  );
};

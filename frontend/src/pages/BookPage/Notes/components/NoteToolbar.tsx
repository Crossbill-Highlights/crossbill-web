import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip.tsx';
import {
  CopyIcon,
  DeleteIcon,
  EditIcon,
  FlashcardsFilledIcon,
  FlashcardsIcon,
} from '@/theme/Icons.tsx';
import { Box } from '@mui/material';

interface NoteToolbarProps {
  onEdit: () => void;
  onCopy: () => void;
  onDelete: () => void;
  flashcardVisible: boolean;
  onFlashcardToggle: () => void;
  disabled?: boolean;
}

export const NoteToolbar = ({
  onEdit,
  onCopy,
  onDelete,
  flashcardVisible,
  onFlashcardToggle,
  disabled = false,
}: NoteToolbarProps) => (
  <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
    <IconButtonWithTooltip
      title={flashcardVisible ? 'Hide flashcards' : 'Show flashcards'}
      ariaLabel={flashcardVisible ? 'Hide flashcards' : 'Show flashcards'}
      onClick={onFlashcardToggle}
      disabled={disabled}
      icon={flashcardVisible ? <FlashcardsFilledIcon /> : <FlashcardsIcon />}
    />
    <IconButtonWithTooltip
      title="Edit note"
      ariaLabel="Edit note"
      onClick={onEdit}
      disabled={disabled}
      icon={<EditIcon />}
    />
    <IconButtonWithTooltip
      title="Copy note content"
      ariaLabel="Copy note content"
      onClick={onCopy}
      disabled={disabled}
      icon={<CopyIcon />}
    />
    <IconButtonWithTooltip
      title="Delete note"
      ariaLabel="Delete note"
      onClick={onDelete}
      disabled={disabled}
      icon={<DeleteIcon />}
    />
  </Box>
);

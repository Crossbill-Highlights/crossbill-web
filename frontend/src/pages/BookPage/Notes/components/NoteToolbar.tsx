import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip.tsx';
import { CopyIcon, DeleteIcon, EditIcon } from '@/theme/Icons.tsx';
import { Box } from '@mui/material';

interface NoteToolbarProps {
  onEdit: () => void;
  onCopy: () => void;
  onDelete: () => void;
  disabled?: boolean;
}

export const NoteToolbar = ({ onEdit, onCopy, onDelete, disabled = false }: NoteToolbarProps) => (
  <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
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

import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip.tsx';
import { DialogToolbar } from '@/components/dialogs/DialogToolbar.tsx';
import { CopyIcon, DeleteIcon, EditIcon, LinkIcon } from '@/theme/Icons.tsx';

interface NoteToolbarProps {
  onCopyLink: () => void;
  onEdit: () => void;
  onCopy: () => void;
  onDelete: () => void;
  disabled?: boolean;
}

export const NoteToolbar = ({
  onCopyLink,
  onEdit,
  onCopy,
  onDelete,
  disabled = false,
}: NoteToolbarProps) => (
  <DialogToolbar>
    <IconButtonWithTooltip
      title="Copy link"
      ariaLabel="Copy link to note"
      onClick={onCopyLink}
      disabled={disabled}
      icon={<LinkIcon />}
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
  </DialogToolbar>
);

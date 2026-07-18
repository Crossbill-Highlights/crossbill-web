import { IconButton, Tooltip, type IconButtonProps } from '@mui/material';
import type { ReactNode } from 'react';

interface IconButtonWithTooltipProps {
  title: string;
  onClick: (e: React.MouseEvent) => void;
  disabled?: boolean;
  ariaLabel?: string;
  icon: ReactNode;
  edge?: IconButtonProps['edge'];
  sx?: IconButtonProps['sx'];
}

export const IconButtonWithTooltip = ({
  title,
  onClick,
  disabled,
  ariaLabel,
  icon,
  edge,
  sx,
}: IconButtonWithTooltipProps) => {
  return (
    <Tooltip title={title}>
      <IconButton
        onClick={onClick}
        disabled={disabled}
        aria-label={ariaLabel}
        size="small"
        edge={edge}
        sx={sx}
      >
        {icon}
      </IconButton>
    </Tooltip>
  );
};

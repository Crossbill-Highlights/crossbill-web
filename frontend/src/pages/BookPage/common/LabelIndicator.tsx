import type { HighlightLabel } from '@/api/generated/model';
import { Box, Chip } from '@mui/material';

interface LabelIndicatorProps {
  label: HighlightLabel | null | undefined;
  onClick?: (event: React.MouseEvent<HTMLElement>) => void;
  size?: 'small' | 'medium';
}

const getContrastColor = (hexColor: string): string => {
  const hex = hexColor.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5 ? '#000000' : '#FFFFFF';
};

export const LabelIndicator = ({ label, onClick, size = 'small' }: LabelIndicatorProps) => {
  if (!label?.ui_color) {
    return null;
  }

  const isClickable = !!onClick;
  const dotSize = size === 'small' ? 10 : 14;

  if (label.text) {
    return (
      <Chip
        label={label.text}
        size="small"
        onClick={onClick}
        sx={{
          backgroundColor: label.ui_color,
          color: getContrastColor(label.ui_color),
          fontWeight: 500,
          fontSize: size === 'small' ? '0.7rem' : '0.8rem',
          height: size === 'small' ? 22 : 26,
          cursor: isClickable ? 'pointer' : 'default',
          '&:hover': isClickable ? { opacity: 0.85 } : {},
        }}
      />
    );
  }

  return (
    <Box
      onClick={onClick}
      sx={{
        width: dotSize,
        height: dotSize,
        borderRadius: '50%',
        backgroundColor: label.ui_color,
        flexShrink: 0,
        cursor: isClickable ? 'pointer' : 'default',
        transition: 'transform 0.15s',
        '&:hover': isClickable ? { transform: 'scale(1.3)' } : {},
      }}
    />
  );
};

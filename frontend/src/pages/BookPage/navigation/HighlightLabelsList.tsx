import { useGetBookHighlightLabelsApiV1BooksBookIdHighlightLabelsGet } from '@/api/generated/highlight-labels/highlight-labels.ts';
import type { HighlightLabelInBook } from '@/api/generated/model';
import { PaletteIcon } from '@/theme/Icons.tsx';
import { getContrastColor } from '@/utils/colorUtils.ts';
import { Box, Chip, Typography } from '@mui/material';

interface HighlightLabelsListProps {
  bookId: number;
  selectedLabelId?: number | null;
  onLabelClick: (labelId: number | null) => void;
  hideTitle?: boolean;
}

const getLabelDisplayName = (label: HighlightLabelInBook): string => {
  if (label.label) {
    return label.label;
  }
  const parts = [label.device_color, label.device_style].filter(Boolean);
  return parts.length > 0 ? parts.join(' / ') : 'Unknown';
};

const getLabelColor = (label: HighlightLabelInBook): string => {
  return label.ui_color || '#6B7280';
};

const LabelChip = ({
  label,
  isSelected,
  onClick,
}: {
  label: HighlightLabelInBook;
  isSelected: boolean;
  onClick: () => void;
}) => {
  const color = getLabelColor(label);
  const displayName = getLabelDisplayName(label);
  const chipLabel = `${displayName} (${label.highlight_count})`;

  return (
    <Chip
      label={
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: color,
              flexShrink: 0,
            }}
          />
          <span>{chipLabel}</span>
        </Box>
      }
      size="small"
      variant={isSelected ? 'filled' : 'outlined'}
      onClick={onClick}
      sx={{
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        py: 0.25,
        px: 0.5,
        ...(isSelected
          ? {
              backgroundColor: color,
              color: getContrastColor(color),
              '&:hover': {
                backgroundColor: color,
                opacity: 0.85,
                transform: 'translateY(-1px)',
              },
            }
          : {
              borderColor: 'divider',
              '&:hover': {
                bgcolor: 'action.hover',
                borderColor: 'secondary.light',
                transform: 'translateY(-1px)',
              },
            }),
      }}
    />
  );
};

export const HighlightLabelsList = ({
  bookId,
  selectedLabelId,
  onLabelClick,
  hideTitle,
}: HighlightLabelsListProps) => {
  const { data: labels } = useGetBookHighlightLabelsApiV1BooksBookIdHighlightLabelsGet(bookId);

  if (!labels || labels.length < 2) {
    return null;
  }

  return (
    <Box>
      {!hideTitle && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            mb: 2,
            pb: 1.5,
          }}
        >
          <PaletteIcon sx={{ fontSize: 18, color: 'primary.main' }} />
          <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
            Labels
          </Typography>
        </Box>
      )}

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
        {labels.map((label) => (
          <LabelChip
            key={label.id}
            label={label}
            isSelected={selectedLabelId === label.id}
            onClick={() => onLabelClick(selectedLabelId === label.id ? null : label.id)}
          />
        ))}
      </Box>
    </Box>
  );
};

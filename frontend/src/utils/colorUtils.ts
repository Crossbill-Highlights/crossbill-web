export const getContrastColor = (hexColor: string): string => {
  const hex = hexColor.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.6 ? '#000000' : '#FFFFFF';
};

export const LABEL_COLORS = [
  '#F59E0B', // Yellow (KOReader)
  '#F97316', // Orange (KOReader)
  '#EF4444', // Red (KOReader)
  '#EC4899', // Pink
  '#8B5CF6', // Purple (KOReader)
  '#6366F1', // Indigo
  '#3B82F6', // Blue (KOReader)
  '#06B6D4', // Cyan (KOReader)
  '#14B8A6', // Teal
  '#10B981', // Green (KOReader)
  '#84CC16', // Olive (KOReader)
  '#059669', // Emerald
  '#6B7280', // Gray (KOReader)
  '#475569', // Slate
];

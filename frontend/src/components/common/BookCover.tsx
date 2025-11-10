import MenuBookIcon from '@mui/icons-material/MenuBook';
import { Box, type SxProps, type Theme, useTheme } from '@mui/material';

export interface BookCoverProps {
  coverPath: string | null | undefined;
  title: string;
  /**
   * Width of the cover container
   */
  width?: number | string | { xs?: number | string; sm?: number | string };
  /**
   * Height of the cover container
   */
  height?: number | string | { xs?: number | string; sm?: number | string };
  /**
   * Object fit for the image ('contain' | 'cover')
   * @default 'contain'
   */
  objectFit?: 'contain' | 'cover';
  /**
   * Border radius
   * @default 2
   */
  borderRadius?: number;
  /**
   * Use gradient background for placeholder instead of solid color
   * @default false
   */
  gradientPlaceholder?: boolean;
  /**
   * Additional sx props for the container
   */
  sx?: SxProps<Theme>;
}

export const BookCover = ({
  coverPath,
  title,
  width = '100%',
  height = 200,
  objectFit = 'contain',
  borderRadius = 2,
  gradientPlaceholder = false,
  sx,
}: BookCoverProps) => {
  const theme = useTheme();
  // Get the API base URL for cover images
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const coverUrl = coverPath ? `${apiUrl}${coverPath}` : null;

  const placeholderBackground = gradientPlaceholder
    ? `linear-gradient(135deg, ${theme.palette.primary.light} 0%, ${theme.palette.primary.dark} 100%)`
    : theme.palette.action.hover;

  return (
    <Box
      sx={{
        width,
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: coverUrl ? 'transparent' : placeholderBackground,
        overflow: 'hidden',
        borderRadius,
        ...sx,
      }}
    >
      {coverUrl ? (
        <img
          src={coverUrl}
          alt={`${title} cover`}
          style={{
            width: '100%',
            height: '100%',
            objectFit,
          }}
          onError={(e) => {
            // Fallback to placeholder if image fails to load
            e.currentTarget.style.display = 'none';
            const placeholder = e.currentTarget.nextSibling as HTMLElement;
            if (placeholder) placeholder.style.display = 'flex';
          }}
        />
      ) : null}
      {/* Placeholder icon when no cover is available */}
      <Box
        sx={{
          display: coverUrl ? 'none' : 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
          height: '100%',
        }}
      >
        <MenuBookIcon
          sx={{
            fontSize: typeof height === 'number' ? height * 0.4 : 80,
            color: gradientPlaceholder ? 'white' : 'text.disabled',
            opacity: gradientPlaceholder ? 0.7 : 1,
          }}
        />
      </Box>
    </Box>
  );
};

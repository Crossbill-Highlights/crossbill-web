import { BookCoverIcon } from '@/theme/Icons.tsx';
import { Box, type SxProps, type Theme, useTheme } from '@mui/material';

export interface BookCoverProps {
  coverFile: string | null;
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
   * Additional sx props for the container
   */
  sx?: SxProps<Theme>;
}

export const BookCover = ({
  coverFile,
  title,
  width = '100%',
  height = 200,
  objectFit = 'contain',
  sx,
}: BookCoverProps) => {
  const theme = useTheme();
  const apiUrl =
    import.meta.env.VITE_API_URL !== undefined
      ? import.meta.env.VITE_API_URL
      : 'http://localhost:8000';

  const coverUrl = coverFile ? `${apiUrl}/api/v1/covers/${coverFile}` : null;
  const placeholderBackground = theme.palette.action.hover;
  const showPlaceholder = !coverUrl;

  return (
    <Box
      sx={{
        width,
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: showPlaceholder ? placeholderBackground : 'transparent',
        overflow: 'hidden',
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
            e.currentTarget.style.display = 'none';
            const placeholder = e.currentTarget.nextSibling as HTMLElement | null;
            if (placeholder) placeholder.style.display = 'flex';
          }}
        />
      ) : null}

      <Box
        sx={{
          display: showPlaceholder ? 'flex' : 'none',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
          height: '100%',
        }}
      >
        <BookCoverIcon
          sx={{
            fontSize: typeof height === 'number' ? height * 0.4 : 80,
            color: 'text.disabled',
            opacity: 1,
          }}
        />
      </Box>
    </Box>
  );
};

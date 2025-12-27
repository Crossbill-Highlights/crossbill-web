import { BookCoverIcon } from '@/components/common/Icons';
import { useAuthenticatedImage } from '@/hooks/useAuthenticatedImage';
import { Box, CircularProgress, type SxProps, type Theme, useTheme } from '@mui/material';

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
  sx,
}: BookCoverProps) => {
  const theme = useTheme();
  // Get the API base URL for cover images
  // Use empty string in production for same-origin requests
  const apiUrl =
    import.meta.env.VITE_API_URL !== undefined
      ? import.meta.env.VITE_API_URL
      : 'http://localhost:8000';

  // For authenticated URLs, fetch as blob with auth headers
  const { objectUrl, loading, error } = useAuthenticatedImage(
    coverPath ? `${apiUrl}${coverPath}` : null
  );

  // Determine final URL to use
  const coverUrl = objectUrl;

  const placeholderBackground = theme.palette.action.hover;
  const showPlaceholder = !coverUrl || error;

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
      {/* Show loading spinner while fetching authenticated image */}
      {loading && (
        <CircularProgress
          size={typeof height === 'number' ? Math.min(height * 0.3, 40) : 40}
          sx={{ color: 'text.disabled' }}
        />
      )}

      {/* Show image when loaded */}
      {!loading && coverUrl && (
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
      )}

      {/* Placeholder icon when no cover is available or on error */}
      <Box
        sx={{
          display: !loading && showPlaceholder ? 'flex' : 'none',
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

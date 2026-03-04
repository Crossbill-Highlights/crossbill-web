import type { BookDetails } from '@/api/generated/model';
import { useGetBookReadingSessionsApiV1BooksBookIdReadingSessionsGet } from '@/api/generated/reading-sessions/reading-sessions';
import { formatDate } from '@/utils/date';
import { Box, Card, Divider, LinearProgress, Typography } from '@mui/material';

interface StatItemProps {
  value: string;
  label: string;
  sublabel?: string;
  progress?: number; // 0-100, only for progress stat
}

const StatItem = ({ value, label, sublabel, progress }: StatItemProps) => (
  <Box
    sx={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      py: 1.5,
      px: 2,
      minWidth: 0,
    }}
  >
    <Typography variant="h6" component="span" sx={{ fontWeight: 'bold' }}>
      {value}
    </Typography>
    <Typography
      variant="caption"
      sx={{
        color: 'text.secondary',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        fontSize: '0.7rem',
      }}
    >
      {label}
    </Typography>
    {progress !== undefined && (
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{ width: '100%', mt: 0.5, borderRadius: 1 }}
      />
    )}
    {sublabel && (
      <Typography variant="caption" sx={{ color: 'text.disabled', fontSize: '0.65rem', mt: 0.25 }}>
        {sublabel}
      </Typography>
    )}
  </Box>
);

interface BookStatsStripProps {
  book: BookDetails;
}

export const BookStatsStrip = ({ book }: BookStatsStripProps) => {
  const { data: sessionsData } = useGetBookReadingSessionsApiV1BooksBookIdReadingSessionsGet(
    book.id,
    {
      limit: 1,
    }
  );

  // Calculate progress percentage
  const progress =
    book.reading_position && book.end_position && book.end_position.index > 0
      ? Math.min(100, Math.round((book.reading_position.index / book.end_position.index) * 100))
      : 0;

  // Count highlights across all chapters
  const highlightCount = book.chapters.reduce((sum, chapter) => sum + chapter.highlights.length, 0);

  // Count flashcards
  const flashcardCount = book.book_flashcards?.length ?? 0;

  // Last read date from latest session
  const latestSession = sessionsData?.sessions[0];
  const lastReadDate = latestSession ? formatDate(latestSession.start_time) : '—';

  // Started date from book creation
  const startedDate = formatDate(book.created_at);

  return (
    <Card
      variant="outlined"
      sx={{
        display: 'flex',
        flexWrap: { xs: 'wrap', sm: 'nowrap' },
      }}
    >
      <Box
        sx={{
          flex: { xs: '1 1 50%', sm: '1 1 0' },
          minWidth: 0,
        }}
      >
        <StatItem value={`${progress}%`} label="Progress" progress={progress} />
      </Box>

      <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />
      {/* Zero-width divider acts as a flex spacer to keep items aligned in the 2x2 mobile grid */}
      <Divider sx={{ display: { xs: 'block', sm: 'none' }, width: '0' }} />

      <Box sx={{ flex: { xs: '1 1 50%', sm: '1 1 0' }, minWidth: 0 }}>
        <StatItem value={String(highlightCount)} label="Highlights" />
      </Box>

      {/* Full-width divider between rows on mobile */}
      <Box
        sx={{
          display: { xs: 'block', sm: 'none' },
          flexBasis: '100%',
          height: 0,
        }}
      >
        <Divider />
      </Box>

      <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />

      <Box sx={{ flex: { xs: '1 1 50%', sm: '1 1 0' }, minWidth: 0 }}>
        <StatItem value={String(flashcardCount)} label="Flashcards" />
      </Box>

      <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />
      {/* Zero-width divider acts as a flex spacer to keep items aligned in the 2x2 mobile grid */}
      <Divider sx={{ display: { xs: 'block', sm: 'none' }, width: '0' }} />

      <Box sx={{ flex: { xs: '1 1 50%', sm: '1 1 0' }, minWidth: 0 }}>
        <StatItem value={lastReadDate} label="Last Read" sublabel={`started ${startedDate}`} />
      </Box>
    </Card>
  );
};

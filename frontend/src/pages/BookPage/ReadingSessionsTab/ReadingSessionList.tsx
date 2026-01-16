import type { ReadingSession } from '@/api/generated/model';
import { FadeInOut } from '@/components/animations/FadeInOut';
import { Box, Typography } from '@mui/material';
import { ReadingSessionCard } from './ReadingSessionCard';

interface ReadingSessionListProps {
  sessions: ReadingSession[];
  emptyMessage?: string;
  animationKey?: string;
}

export const ReadingSessionList = ({
  sessions,
  emptyMessage = 'No reading sessions recorded yet.',
  animationKey = 'reading-sessions',
}: ReadingSessionListProps) => {
  return (
    <FadeInOut ekey={animationKey}>
      {sessions.length === 0 ? (
        <Typography variant="body1" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
          {emptyMessage}
        </Typography>
      ) : (
        <Box
          component="ul"
          sx={{ display: 'flex', flexDirection: 'column', listStyle: 'none', p: 0, m: 0 }}
          aria-label="Reading sessions"
        >
          {sessions.map((session) => (
            <ReadingSessionCard key={session.id} session={session} />
          ))}
        </Box>
      )}
    </FadeInOut>
  );
};

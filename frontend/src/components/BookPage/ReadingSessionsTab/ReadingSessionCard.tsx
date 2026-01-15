import type { ReadingSession } from '@/api/generated/model';
import { useGetReadingSessionAiSummaryApiV1ReadingSessionsReadingSessionIdAiSummaryGet } from '@/api/generated/reading-sessions/reading-sessions';
import { AIFeature } from '@/components/common/AIFeature';
import { useSettings } from '@/context/SettingsContext';
import { useSnackbar } from '@/context/SnackbarContext';
import { formatDate, formatDuration, formatTime } from '@/utils/date';
import { Box, Button, Typography } from '@mui/material';
import type { AxiosError } from 'axios';
import { useEffect } from 'react';
import { AISummary } from './AISummary';

interface SessionMetadataProps {
  startTime: string;
  endTime: string;
  startPage: number | null | undefined;
  endPage: number | null | undefined;
}

const SessionMetadata = ({ startTime, endTime, startPage, endPage }: SessionMetadataProps) => {
  const pagesRead = startPage != null && endPage != null ? endPage - startPage : 0;

  return (
    <Box
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: 1.5,
        mb: 1.5,
      }}
    >
      <Typography
        variant="body2"
        sx={{
          color: 'text.secondary',
        }}
      >
        <span>
          {formatDate(startTime)}
          &nbsp;&nbsp;•&nbsp;&nbsp;{formatTime(startTime)}
          &nbsp;&nbsp;•&nbsp;&nbsp;{formatDuration(startTime, endTime)}
        </span>
        {startPage != null && endPage != null && (
          <span>
            &nbsp;&nbsp;•&nbsp;&nbsp;Pages {startPage}-{endPage}
            {pagesRead > 0 && ` (${pagesRead} page${pagesRead !== 1 ? 's' : ''})`}
          </span>
        )}
      </Typography>
    </Box>
  );
};

interface ReadingSessionCardProps {
  session: ReadingSession;
  component?: React.ElementType;
}

interface SummaryPlaceholderProps {
  onGenerate: () => void;
  isLoading: boolean;
}

const SummaryPlaceholder = ({ onGenerate, isLoading }: SummaryPlaceholderProps) => (
  <Box
    sx={{
      padding: 1.5,
    }}
  >
    <Button onClick={onGenerate} disabled={isLoading} variant="contained" sx={{ borderRadius: 2 }}>
      {isLoading ? 'Generating...' : 'Generate Summary'}
    </Button>
  </Box>
);

export const ReadingSessionCard = ({ session }: ReadingSessionCardProps) => {
  const { showSnackbar } = useSnackbar();

  const { data, isLoading, error, refetch } =
    useGetReadingSessionAiSummaryApiV1ReadingSessionsReadingSessionIdAiSummaryGet(session.id, {
      query: {
        enabled: false,
        retry: false,
      },
    });

  useEffect(() => {
    if (error) {
      const axiosError = error as AxiosError;
      const errorMessage =
        axiosError.response?.status === 400
          ? 'Cannot generate summary - no content available for this session'
          : 'Failed to generate summary. Please try again.';
      showSnackbar(errorMessage, 'error');
    }
  }, [error, showSnackbar]);

  const summary = session.ai_summary || data?.summary;
  const hasSummary = Boolean(summary);
  const aiEnabled = !!useSettings().settings?.ai_features;

  return (
    <li key={session.id}>
      <Box
        sx={{
          py: aiEnabled ? 3.5 : 1,
          px: 2.5,
          '@media (max-width: 768px)': {
            px: 2,
            py: 2,
          },
        }}
      >
        <SessionMetadata
          startTime={session.start_time}
          endTime={session.end_time}
          startPage={session.start_page}
          endPage={session.end_page}
        />

        <AIFeature>
          {hasSummary ? (
            <AISummary summary={summary} />
          ) : (
            <SummaryPlaceholder onGenerate={() => refetch()} isLoading={isLoading} />
          )}
        </AIFeature>
      </Box>
    </li>
  );
};

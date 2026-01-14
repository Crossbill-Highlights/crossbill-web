import type { ReadingSession } from '@/api/generated/model';
import { useGetReadingSessionAiSummaryApiV1ReadingSessionsReadingSessionIdAiSummaryGet } from '@/api/generated/reading-sessions/reading-sessions';
import { AIFeature } from '@/components/common/AIFeature';
import { AISummaryIcon, DateIcon, DurationIcon, TimeIcon } from '@/components/common/Icons.tsx';
import { ToolbarIconButton } from '@/components/common/ToolbarIconButton';
import { formatDate, formatDuration, formatTime } from '@/utils/date';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useState } from 'react';
import { AISummary } from './AISummary';

interface SessionDateProps {
  startTime: string;
}

const SessionDate = ({ startTime }: SessionDateProps) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    <DateIcon
      sx={{
        fontSize: 18,
        color: 'text.secondary',
        opacity: 0.7,
      }}
    />
    <Typography variant="body1">{formatDate(startTime)}</Typography>
  </Box>
);

interface SessionStartTimeProps {
  startTime: string;
}

const SessionStartTime = ({ startTime }: SessionStartTimeProps) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    <TimeIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
    <Typography variant="body1" color="text.secondary">
      {formatTime(startTime)}
    </Typography>
  </Box>
);

interface SessionDurationProps {
  startTime: string;
  endTime: string;
}

const SessionDuration = ({ startTime, endTime }: SessionDurationProps) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    <DurationIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
    <Typography variant="body1" color="text.secondary">
      {formatDuration(startTime, endTime)}
    </Typography>
  </Box>
);

interface SessionPageRangeProps {
  startPage: number;
  endPage: number;
}

const SessionPageRange = ({ startPage, endPage }: SessionPageRangeProps) => {
  const pagesRead = endPage - startPage;

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        pl: 0.5,
      }}
    >
      <MenuBookIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
      <Typography variant="body1">
        Pages {startPage} - {endPage}
        {pagesRead > 0 && ` (${pagesRead} pages)`}
      </Typography>
    </Box>
  );
};

interface ReadingSessionCardProps {
  session: ReadingSession;
  component?: React.ElementType;
}

export const ReadingSessionCard = ({ session }: ReadingSessionCardProps) => {
  const hasPageInfo = session.start_page != null && session.end_page != null;
  const [shouldFetch, setShouldFetch] = useState(false);

  const { data, isLoading, error } =
    useGetReadingSessionAiSummaryApiV1ReadingSessionsReadingSessionIdAiSummaryGet(session.id, {
      query: {
        enabled: shouldFetch && !session.ai_summary,
      },
    });

  const summary = session.ai_summary || data?.summary;
  const hasSummary = Boolean(summary);

  return (
    <li key={session.id}>
      <Box
        sx={{
          py: 2.5,
          px: 2.5,
          borderBottom: 1,
          borderColor: 'divider',
          '&:last-child': {
            borderBottom: 0,
          },
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 3,
            flexWrap: 'wrap',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 3,
              flexWrap: 'wrap',
            }}
          >
            <SessionDate startTime={session.start_time} />
            <SessionStartTime startTime={session.start_time} />
            <SessionDuration startTime={session.start_time} endTime={session.end_time} />
            {hasPageInfo && (
              <SessionPageRange startPage={session.start_page!} endPage={session.end_page!} />
            )}
          </Box>

          <AIFeature>
            {!hasSummary && (
              <ToolbarIconButton
                title="Generate AI Summary"
                onClick={() => setShouldFetch(true)}
                disabled={isLoading}
                ariaLabel="Generate AI summary for this reading session"
                icon={
                  isLoading ? (
                    <CircularProgress size={16} sx={{ color: 'primary.main' }} />
                  ) : (
                    <AISummaryIcon sx={{ fontSize: 18 }} />
                  )
                }
              />
            )}
          </AIFeature>
        </Box>

        <AIFeature>
          <AISummary summary={summary} error={error} />
        </AIFeature>
      </Box>
    </li>
  );
};

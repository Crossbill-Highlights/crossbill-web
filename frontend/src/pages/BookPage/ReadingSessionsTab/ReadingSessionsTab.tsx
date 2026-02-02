import { useGetHighlightTagsApiV1BooksBookIdHighlightTagsGet } from '@/api/generated/highlights/highlights';
import { useGetBookReadingSessionsApiV1BooksBookIdReadingSessionsGet } from '@/api/generated/reading-sessions/reading-sessions';
import type { BookDetails, ReadingSession } from '@/api/generated/model';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { ThreeColumnLayout } from '@/components/layout/Layouts';
import { HighlightViewModal } from '@/pages/BookPage/HighlightsTab/HighlightViewModal/HighlightViewModal';
import { useHighlightModal } from '@/pages/BookPage/HighlightsTab/hooks/useHighlightModal';
import { Alert, Box, Pagination } from '@mui/material';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { keyBy } from 'lodash';
import { useMemo, useState } from 'react';
import { ReadingSessionList } from './ReadingSessionList';

const SESSIONS_PER_PAGE = 30;

interface ReadingSessionsTabProps {
  book: BookDetails;
  isDesktop: boolean;
}

export const ReadingSessionsTab = ({ book, isDesktop }: ReadingSessionsTabProps) => {
  const { sessionPage } = useSearch({ from: '/book/$bookId' });
  const navigate = useNavigate({ from: '/book/$bookId' });

  const currentPage = sessionPage || 1;
  const offset = (currentPage - 1) * SESSIONS_PER_PAGE;

  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);

  const bookmarksByHighlightId = useMemo(
    () => keyBy(book.bookmarks, 'highlight_id'),
    [book.bookmarks]
  );

  const { data: tagsResponse } = useGetHighlightTagsApiV1BooksBookIdHighlightTagsGet(book.id);

  const { data, isLoading, isError } = useGetBookReadingSessionsApiV1BooksBookIdReadingSessionsGet(
    book.id,
    { limit: SESSIONS_PER_PAGE, offset }
  );

  const activeSession = useMemo(
    () => data?.sessions.find((s: ReadingSession) => s.id === activeSessionId) || null,
    [data?.sessions, activeSessionId]
  );

  const sessionHighlights = useMemo(() => activeSession?.highlights || [], [activeSession]);

  const {
    openHighlightId,
    currentHighlight,
    currentHighlightIndex,
    handleOpenHighlight,
    handleCloseHighlight,
    handleModalNavigate,
  } = useHighlightModal({ allHighlights: sessionHighlights, isMobile: !isDesktop });

  const handleOpenSessionHighlight = (sessionId: number, highlightId: number) => {
    setActiveSessionId(sessionId);
    handleOpenHighlight(highlightId);
  };

  const handleCloseModal = (lastViewedHighlightId?: number) => {
    handleCloseHighlight(lastViewedHighlightId);
    setActiveSessionId(null);
  };

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    navigate({
      search: (prev) => ({
        ...prev,
        sessionPage: value === 1 ? undefined : value,
      }),
      replace: true,
    });
  };

  const totalPages = data?.total ? Math.ceil(data.total / SESSIONS_PER_PAGE) : 0;

  const content = (
    <Box>
      {isLoading && <Spinner />}

      {isError && (
        <Box sx={{ py: 3 }}>
          <Alert severity="error">Failed to load reading sessions. Please try again later.</Alert>
        </Box>
      )}

      {data && (
        <>
          <ReadingSessionList
            sessions={data.sessions}
            animationKey={`reading-sessions-${currentPage}`}
            bookmarksByHighlightId={bookmarksByHighlightId}
            onOpenHighlight={handleOpenSessionHighlight}
          />
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={totalPages}
                page={currentPage}
                onChange={handlePageChange}
                color="primary"
                size="large"
                showFirstButton
                showLastButton
              />
            </Box>
          )}
        </>
      )}
    </Box>
  );

  if (!isDesktop) {
    return (
      <>
        <Box sx={{ maxWidth: '800px', mx: 'auto' }}>{content}</Box>
        {currentHighlight && (
          <HighlightViewModal
            highlight={currentHighlight}
            bookId={book.id}
            open={!!openHighlightId}
            onClose={handleCloseModal}
            availableTags={tagsResponse?.tags || []}
            bookmarksByHighlightId={bookmarksByHighlightId}
            allHighlights={sessionHighlights}
            currentIndex={currentHighlightIndex}
            onNavigate={handleModalNavigate}
          />
        )}
      </>
    );
  }

  return (
    <>
      <ThreeColumnLayout>
        <div></div>
        {content}
        <div></div>
      </ThreeColumnLayout>
      {currentHighlight && (
        <HighlightViewModal
          highlight={currentHighlight}
          bookId={book.id}
          open={!!openHighlightId}
          onClose={handleCloseModal}
          availableTags={tagsResponse?.tags || []}
          bookmarksByHighlightId={bookmarksByHighlightId}
          allHighlights={sessionHighlights}
          currentIndex={currentHighlightIndex}
          onNavigate={handleModalNavigate}
        />
      )}
    </>
  );
};

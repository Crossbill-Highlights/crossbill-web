import { useGetBookReadingSessionsApiV1BooksBookIdReadingSessionsGet } from '@/api/generated/books/books';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { ThreeColumnLayout } from '@/components/layout/Layouts';
import { Alert, Box, Pagination } from '@mui/material';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { ReadingSessionList } from './ReadingSessionList';

const SESSIONS_PER_PAGE = 30;

interface ReadingSessionsTabProps {
  bookId: number;
  isDesktop: boolean;
}

export const ReadingSessionsTab = ({ bookId, isDesktop }: ReadingSessionsTabProps) => {
  const { sessionPage } = useSearch({ from: '/book/$bookId' });
  const navigate = useNavigate({ from: '/book/$bookId' });

  const currentPage = sessionPage || 1;
  const offset = (currentPage - 1) * SESSIONS_PER_PAGE;

  const { data, isLoading, isError } = useGetBookReadingSessionsApiV1BooksBookIdReadingSessionsGet(
    bookId,
    { limit: SESSIONS_PER_PAGE, offset }
  );

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
    return <Box sx={{ maxWidth: '800px', mx: 'auto' }}>{content}</Box>;
  }

  return (
    <ThreeColumnLayout>
      <div></div>
      {content}
      <div></div>
    </ThreeColumnLayout>
  );
};

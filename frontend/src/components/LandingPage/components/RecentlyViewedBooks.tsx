import { useGetRecentlyViewedBooksApiV1BooksRecentlyViewedGet } from '@/api/generated/books/books';
import { Alert, Box } from '@mui/material';
import { SectionTitle } from '../../common/SectionTitle';
import { Spinner } from '../../common/Spinner';
import { BookList } from './BookList';

const RECENTLY_VIEWED_LIMIT = 10;

export const RecentlyViewedBooks = () => {
  const { data, isLoading, isError } = useGetRecentlyViewedBooksApiV1BooksRecentlyViewedGet({
    limit: RECENTLY_VIEWED_LIMIT,
  });

  // Don't render the section if there are no recently viewed books
  if (!isLoading && !isError && (!data?.books || data.books.length === 0)) {
    return null;
  }

  return (
    <Box sx={{ mb: 6 }}>
      <SectionTitle showDivider>Recently Viewed</SectionTitle>

      {isLoading && <Spinner />}

      {isError && (
        <Box sx={{ py: 3 }}>
          <Alert severity="error">Failed to load recently viewed books.</Alert>
        </Box>
      )}

      {data?.books && data.books.length > 0 && (
        <BookList books={data.books} pageKey="recently-viewed" />
      )}
    </Box>
  );
};

import { Alert, Box, Container, Pagination, Typography } from '@mui/material';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useGetBooksApiV1HighlightsBooksGet } from '../../api/generated/highlights/highlights';
import { SearchBar } from '../common/SearchBar';
import { SectionTitle } from '../common/SectionTitle';
import { Spinner } from '../common/Spinner';
import { BookList } from './components/BookList';

const BOOKS_PER_PAGE = 30;

export const LandingPage = () => {
  const navigate = useNavigate({ from: '/' });
  const { search, page } = useSearch({ from: '/' });
  const searchText = search || '';
  const currentPage = page || 1;

  // Calculate offset for pagination
  const offset = (currentPage - 1) * BOOKS_PER_PAGE;

  const { data, isLoading, isError } = useGetBooksApiV1HighlightsBooksGet({
    search: searchText || undefined,
    offset,
    limit: BOOKS_PER_PAGE,
  });

  const handleSearch = (value: string) => {
    navigate({
      search: (prev) => ({
        ...prev,
        search: value || undefined,
        page: 1, // Reset to first page when searching
      }),
      replace: true,
    });
  };

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    navigate({
      search: (prev) => ({
        ...prev,
        page: value,
      }),
      replace: true,
    });
  };

  // Calculate total pages
  const totalPages = data?.total ? Math.ceil(data.total / BOOKS_PER_PAGE) : 0;

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: { xs: 6, md: 8 }, mb: 6, textAlign: 'center' }}>
        <Typography variant="h2" component="h1" gutterBottom>
          Welcome to Crossbill
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ fontSize: '1.1rem' }}>
          Your highlights management application
        </Typography>
      </Box>

      <Box sx={{ mb: 4 }}>
        <SectionTitle showDivider>Books</SectionTitle>

        <Box sx={{ mb: 3 }}>
          <SearchBar
            onSearch={handleSearch}
            placeholder="Search books by title or author..."
            initialValue={searchText}
          />
        </Box>

        {isLoading && <Spinner />}

        {isError && (
          <Box sx={{ py: 3 }}>
            <Alert severity="error">Failed to load books. Please try again later.</Alert>
          </Box>
        )}

        {data?.books && data.books.length === 0 && (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              No books found. Upload some highlights to get started!
            </Typography>
          </Box>
        )}

        {data?.books && data.books.length > 0 && (
          <>
            <BookList books={data.books} />
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
    </Container>
  );
};

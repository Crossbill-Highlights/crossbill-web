import { Box } from '@mui/material';
import type { BookWithHighlightCount } from '../../../api/generated/model';
import { BookCard } from './BookCard';

export interface BookListProps {
  books: BookWithHighlightCount[];
}

export const BookList = ({ books }: BookListProps) => {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: {
          xs: 'repeat(auto-fill, minmax(150px, 1fr))',
          sm: 'repeat(auto-fill, minmax(150px, 1fr))',
          md: 'repeat(auto-fill, minmax(150px, 1fr))',
          lg: 'repeat(auto-fill, minmax(150px, 1fr))',
        },
        gap: 3,
        justifyItems: 'start',
      }}
    >
      {books.map((book) => (
        <BookCard key={book.id} book={book} />
      ))}
    </Box>
  );
};

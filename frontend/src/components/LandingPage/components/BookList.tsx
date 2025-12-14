import { Box } from '@mui/material';
import { AnimatePresence, motion } from 'motion/react';
import type { BookWithHighlightCount } from '../../../api/generated/model';
import { BookCard } from './BookCard';

export interface BookListProps {
  books: BookWithHighlightCount[];
  pageKey: string;
}

export const BookList = ({ books, pageKey }: BookListProps) => {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={pageKey}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
      >
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: 'repeat(auto-fill, minmax(150px, 1fr))',
              sm: 'repeat(auto-fill, minmax(150px, 1fr))',
              md: 'repeat(auto-fill, minmax(150px, 1fr))',
              lg: 'repeat(auto-fill, minmax(150px, 1fr))',
            },
            gap: 4,
            justifyItems: 'start',
          }}
        >
          {books.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </Box>
      </motion.div>
    </AnimatePresence>
  );
};

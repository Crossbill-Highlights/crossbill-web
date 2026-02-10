import type {
  BookDetails,
  ChapterWithHighlights,
  Flashcard,
  Highlight,
  HighlightTagInBook,
} from '@/api/generated/model';
import { SearchBar } from '@/components/inputs/SearchBar.tsx';
import { ThreeColumnLayout } from '@/components/layout/Layouts.tsx';
import { ChapterNav, type ChapterNavigationData } from '@/pages/BookPage/navigation/ChapterNav.tsx';
import { MobileNavigation } from '@/pages/BookPage/navigation/MobileNavigation.tsx';
import { SortIcon } from '@/theme/Icons.tsx';
import { Box, IconButton, Tooltip } from '@mui/material';
import { useSearch } from '@tanstack/react-router';
import { flatMap } from 'lodash';
import { useEffect, useMemo, useState } from 'react';
import { HighlightTagsList } from '../navigation/HighlightTagsList.tsx';
import {
  FlashcardChapterList,
  type FlashcardChapterData,
  type FlashcardWithContext,
} from './FlashcardChapterList.tsx';
import { FlashcardEditDialog } from './FlashcardEditDialog.tsx';

const BOOK_FLASHCARDS_KEY = -1;

interface FlashcardsTabProps {
  book: BookDetails;
  isDesktop: boolean;
  onSearch: (value: string) => void;
  onTagClick: (tagId: number | null) => void;
  onChapterClick: (chapterId: number) => void;
}

export const FlashcardsTab = ({
  book,
  isDesktop,
  onSearch,
  onTagClick,
  onChapterClick,
}: FlashcardsTabProps) => {
  const { search: urlSearch, tagId: urlTagId } = useSearch({ from: '/book/$bookId' });

  const searchText = urlSearch || '';
  const [selectedTagId, setSelectedTagId] = useState<number | undefined>(urlTagId);
  const [isReversed, setIsReversed] = useState(false);
  const [editingFlashcard, setEditingFlashcard] = useState<FlashcardWithContext | null>(null);

  useEffect(() => {
    setSelectedTagId(urlTagId);
  }, [urlTagId]);

  const handleTagClick = (newTagId: number | null) => {
    setSelectedTagId(newTagId || undefined);
    onTagClick(newTagId);
  };

  const bookChapters = book.chapters;

  // Extract all flashcards with context from book chapters
  const allFlashcardsWithContext = useMemo((): FlashcardWithContext[] => {
    const highlightFlashcards = flatMap(bookChapters, (chapter: ChapterWithHighlights) =>
      flatMap(chapter.highlights, (highlight: Highlight) =>
        highlight.flashcards.map((flashcard: Flashcard) => ({
          ...flashcard,
          highlight: highlight,
          chapterName: chapter.name || 'Unknown Chapter',
          chapterId: chapter.id,
          highlightTags: highlight.highlight_tags,
        }))
      )
    );

    const bookLevelFlashcards: FlashcardWithContext[] = (book.book_flashcards ?? []).map((fc) => ({
      ...fc,
      highlight: null,
      chapterName: 'Book Flashcards',
      chapterId: null,
      highlightTags: [],
    }));

    return [...highlightFlashcards, ...bookLevelFlashcards];
  }, [bookChapters, book.book_flashcards]);

  // Filter flashcards by tag and search
  const filteredFlashcards = useMemo((): FlashcardWithContext[] => {
    let result = allFlashcardsWithContext;

    // Filter by tag
    if (selectedTagId) {
      result = result.filter((fc) => fc.highlightTags.some((tag) => tag.id === selectedTagId));
    }

    // Filter by search (question or answer)
    if (searchText) {
      const lowerSearch = searchText.toLowerCase();
      result = result.filter(
        (fc) =>
          fc.question.toLowerCase().includes(lowerSearch) ||
          fc.answer.toLowerCase().includes(lowerSearch)
      );
    }

    return result;
  }, [allFlashcardsWithContext, selectedTagId, searchText]);

  // Group flashcards by chapter
  const flashcardChapters = useMemo((): FlashcardChapterData[] => {
    const grouped: Partial<Record<number, FlashcardWithContext[]>> = {};
    for (const fc of filteredFlashcards) {
      const key = fc.chapterId ?? BOOK_FLASHCARDS_KEY;
      if (!grouped[key]) {
        grouped[key] = [];
      }
      grouped[key]!.push(fc);
    }

    // Separate book-level flashcards from chapter flashcards
    const bookFlashcardsGroup = grouped[BOOK_FLASHCARDS_KEY];
    delete grouped[BOOK_FLASHCARDS_KEY];

    const chapterResults = Object.entries(grouped)
      .filter((entry): entry is [string, FlashcardWithContext[]] => entry[1] !== undefined)
      .map(([chapterId, flashcards]) => ({
        id: Number(chapterId),
        name: flashcards[0].chapterName,
        flashcards,
      }));

    // Append book-level flashcards at the end
    if (bookFlashcardsGroup && bookFlashcardsGroup.length > 0) {
      chapterResults.push({
        id: BOOK_FLASHCARDS_KEY,
        name: 'Book Flashcards',
        flashcards: bookFlashcardsGroup,
      });
    }

    if (isReversed) {
      return [...chapterResults].reverse().map((chapter) => ({
        ...chapter,
        flashcards: [...chapter.flashcards].reverse(),
      }));
    }

    return chapterResults;
  }, [filteredFlashcards, isReversed]);

  // Compute empty message based on state
  const emptyMessage = useMemo(() => {
    if (searchText) {
      return selectedTagId
        ? 'No flashcards found matching your search with the selected tag.'
        : 'No flashcards found matching your search.';
    }
    return selectedTagId
      ? 'No flashcards found with the selected tag.'
      : 'No flashcards yet. Create flashcards from your highlights to start studying.';
  }, [searchText, selectedTagId]);

  const navData = useFlashcardsTabData(
    allFlashcardsWithContext,
    flashcardChapters,
    book.highlight_tags,
    selectedTagId
  );

  return (
    <>
      {!isDesktop && (
        <>
          <MobileFlashcardsContent
            searchText={searchText}
            onSearch={onSearch}
            isReversed={isReversed}
            onToggleReverse={() => setIsReversed(!isReversed)}
            chapters={flashcardChapters}
            bookId={book.id}
            emptyMessage={emptyMessage}
            onEditFlashcard={setEditingFlashcard}
          />
          <MobileNavigation
            book={book}
            onTagClick={handleTagClick}
            selectedTag={selectedTagId}
            bookmarks={[]}
            allHighlights={[]}
            onBookmarkClick={() => {}}
            chapters={navData.chapters}
            onChapterClick={onChapterClick}
            displayTags={navData.tags}
            currentTab="flashcards"
          />
        </>
      )}

      {isDesktop && (
        <DesktopFlashcardsContent
          book={book}
          tags={navData.tags}
          selectedTagId={selectedTagId}
          onTagClick={handleTagClick}
          searchText={searchText}
          onSearch={onSearch}
          isReversed={isReversed}
          onToggleReverse={() => setIsReversed(!isReversed)}
          chapters={flashcardChapters}
          navChapters={navData.chapters}
          bookId={book.id}
          emptyMessage={emptyMessage}
          onEditFlashcard={setEditingFlashcard}
          onChapterClick={onChapterClick}
        />
      )}

      {editingFlashcard && (
        <FlashcardEditDialog
          flashcard={editingFlashcard}
          bookId={book.id}
          open={!!editingFlashcard}
          onClose={() => setEditingFlashcard(null)}
        />
      )}
    </>
  );
};

interface MobileFlashcardsContentProps {
  searchText: string;
  onSearch: (value: string) => void;
  isReversed: boolean;
  onToggleReverse: () => void;
  chapters: FlashcardChapterData[];
  bookId: number;
  emptyMessage: string;
  onEditFlashcard: (flashcard: FlashcardWithContext) => void;
}

const MobileFlashcardsContent = ({
  searchText,
  onSearch,
  isReversed,
  onToggleReverse,
  chapters,
  bookId,
  emptyMessage,
  onEditFlashcard,
}: MobileFlashcardsContentProps) => (
  <>
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 3 }}>
      <Box sx={{ flexGrow: 1 }}>
        <SearchBar
          onSearch={onSearch}
          placeholder="Search flashcards..."
          initialValue={searchText}
        />
      </Box>
      <Tooltip title={isReversed ? 'Show oldest first' : 'Show newest first'}>
        <IconButton
          onClick={onToggleReverse}
          sx={{
            mt: '1px',
            color: isReversed ? 'primary.main' : 'text.secondary',
            '&:hover': { color: 'primary.main' },
          }}
        >
          <SortIcon />
        </IconButton>
      </Tooltip>
    </Box>
    <FlashcardChapterList
      chapters={chapters}
      bookId={bookId}
      emptyMessage={emptyMessage}
      animationKey="flashcards"
      onEditFlashcard={onEditFlashcard}
    />
  </>
);

interface DesktopFlashcardsContentProps {
  book: BookDetails;
  tags: HighlightTagInBook[];
  selectedTagId: number | undefined;
  onTagClick: (tagId: number | null) => void;
  searchText: string;
  onSearch: (value: string) => void;
  isReversed: boolean;
  onToggleReverse: () => void;
  chapters: FlashcardChapterData[];
  navChapters: ChapterNavigationData[];
  bookId: number;
  emptyMessage: string;
  onEditFlashcard: (flashcard: FlashcardWithContext) => void;
  onChapterClick: (chapterId: number) => void;
}

const DesktopFlashcardsContent = ({
  book,
  tags,
  selectedTagId,
  onTagClick,
  searchText,
  onSearch,
  isReversed,
  onToggleReverse,
  chapters,
  navChapters,
  bookId,
  emptyMessage,
  onEditFlashcard,
  onChapterClick,
}: DesktopFlashcardsContentProps) => (
  <ThreeColumnLayout>
    <HighlightTagsList
      tags={tags}
      tagGroups={book.highlight_tag_groups}
      bookId={book.id}
      selectedTag={selectedTagId}
      onTagClick={onTagClick}
      hideEmptyGroups
    />

    <Box>
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 3 }}>
        <Box sx={{ flexGrow: 1 }}>
          <SearchBar
            onSearch={onSearch}
            placeholder="Search flashcards..."
            initialValue={searchText}
          />
        </Box>
        <Tooltip title={isReversed ? 'Show oldest first' : 'Show newest first'}>
          <IconButton
            onClick={onToggleReverse}
            sx={{
              mt: '1px',
              color: isReversed ? 'primary.main' : 'text.secondary',
              '&:hover': { color: 'primary.main' },
            }}
          >
            <SortIcon />
          </IconButton>
        </Tooltip>
      </Box>
      <FlashcardChapterList
        chapters={chapters}
        bookId={bookId}
        emptyMessage={emptyMessage}
        animationKey="flashcards"
        onEditFlashcard={onEditFlashcard}
      />
    </Box>

    <ChapterNav chapters={navChapters} onChapterClick={onChapterClick} countType="flashcard" />
  </ThreeColumnLayout>
);

const useFlashcardsTabData = (
  allFlashcardsWithContext: FlashcardWithContext[],
  chapters: FlashcardChapterData[],
  tagsInBook: HighlightTagInBook[] | undefined,
  selectedTagId: number | undefined
) => {
  const tagsWithFlashcards = useMemo(() => {
    if (!tagsInBook) return [];

    const tagIdsWithFlashcards = new Set<number>();
    allFlashcardsWithContext.forEach((fc) =>
      fc.highlightTags.forEach((tag) => tagIdsWithFlashcards.add(tag.id))
    );

    return tagsInBook.filter((tag) => tagIdsWithFlashcards.has(tag.id));
  }, [tagsInBook, allFlashcardsWithContext]);

  const navChapters: ChapterNavigationData[] = useMemo(() => {
    return chapters.map((ch) => ({
      id: ch.id,
      name: ch.name,
      itemCount: ch.flashcards.length,
    }));
  }, [chapters]);

  return {
    chapters: navChapters,
    tags: tagsWithFlashcards,
    selectedTagId,
  };
};

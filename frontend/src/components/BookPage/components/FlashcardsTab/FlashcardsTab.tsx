import type {
  BookDetails,
  ChapterWithHighlights,
  Flashcard,
  Highlight,
  HighlightTagInBook,
} from '@/api/generated/model';
import { ChapterNav } from '@/components/BookPage/components/HighlightsTab/ChapterNav.tsx';
import { scrollToElementWithHighlight } from '@/components/common/animations/scrollUtils.ts';
import { SortIcon } from '@/components/common/Icons.tsx';
import { SearchBar } from '@/components/common/SearchBar.tsx';
import { ThreeColumnLayout } from '@/components/layout/Layouts.tsx';
import { Box, IconButton, Tooltip } from '@mui/material';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { flatMap } from 'lodash';
import { useEffect, useMemo, useState } from 'react';
import { HighlightTags } from '../HighlightTags.tsx';
import {
  FlashcardChapterList,
  type FlashcardChapterData,
  type FlashcardWithContext,
} from './FlashcardChapterList';
import { FlashcardEditDialog } from './FlashcardEditDialog.tsx';

interface FlashcardsTabProps {
  book: BookDetails;
  isDesktop: boolean;
}

export const FlashcardsTab = ({ book, isDesktop }: FlashcardsTabProps) => {
  const { search: urlSearch, tagId: urlTagId } = useSearch({ from: '/book/$bookId' });
  const navigate = useNavigate({ from: '/book/$bookId' });

  const searchText = urlSearch || '';
  const [selectedTagId, setSelectedTagId] = useState<number | undefined>(urlTagId);
  const [isReversed, setIsReversed] = useState(false);
  const [editingFlashcard, setEditingFlashcard] = useState<FlashcardWithContext | null>(null);

  useEffect(() => {
    setSelectedTagId(urlTagId);
  }, [urlTagId]);

  const handleSearch = (value: string) => {
    navigate({
      search: (prev) => ({
        ...prev,
        search: value || undefined,
      }),
      replace: true,
    });
  };

  const handleTagClick = (newTagId: number | null) => {
    setSelectedTagId(newTagId || undefined);
    navigate({
      search: (prev) => ({
        ...prev,
        tagId: newTagId || undefined,
      }),
      replace: true,
    });
  };

  const handleChapterClick = (chapterId: number | string) => {
    if (searchText) {
      navigate({
        search: (prev) => ({
          ...prev,
          search: undefined,
        }),
        replace: true,
      });
    }
    scrollToElementWithHighlight(`chapter-${chapterId}`, { behavior: 'smooth', block: 'start' });
  };

  const bookChapters = book.chapters;

  // Extract all flashcards with context from book chapters
  const allFlashcardsWithContext = useMemo((): FlashcardWithContext[] => {
    if (!bookChapters) return [];

    return flatMap(bookChapters, (chapter: ChapterWithHighlights) =>
      flatMap(chapter.highlights || [], (highlight: Highlight) =>
        (highlight.flashcards || []).map((flashcard: Flashcard) => ({
          ...flashcard,
          highlight: highlight,
          chapterName: chapter.name || 'Unknown Chapter',
          chapterId: chapter.id,
          highlightTags: highlight.highlight_tags,
        }))
      )
    );
  }, [bookChapters]);

  // Filter flashcards by tag and search
  const filteredFlashcards = useMemo((): FlashcardWithContext[] => {
    let result = allFlashcardsWithContext;

    // Filter by tag
    if (selectedTagId) {
      result = result.filter((fc) => fc.highlightTags?.some((tag) => tag.id === selectedTagId));
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
    const grouped: Record<number, FlashcardWithContext[]> = {};
    for (const fc of filteredFlashcards) {
      if (fc.chapterId) {
        if (!grouped[fc.chapterId]) {
          grouped[fc.chapterId] = [];
        }
        grouped[fc.chapterId].push(fc);
      }
    }

    const result = Object.entries(grouped).map(([chapterId, flashcards]) => ({
      id: Number(chapterId),
      name: flashcards[0]?.chapterName || 'Unknown Chapter',
      flashcards,
    }));

    if (isReversed) {
      return [...result].reverse().map((chapter) => ({
        ...chapter,
        flashcards: [...chapter.flashcards].reverse(),
      }));
    }

    return result;
  }, [filteredFlashcards, isReversed]);

  // Tags that have highlights with flashcards
  const bookHighlightTags = book.highlight_tags;
  const tagsWithFlashcards = useMemo(() => {
    if (!bookHighlightTags) return [];

    const tagIdsWithFlashcards = new Set<number>();
    for (const fc of allFlashcardsWithContext) {
      fc.highlightTags?.forEach((tag) => tagIdsWithFlashcards.add(tag.id));
    }

    return bookHighlightTags.filter((tag) => tagIdsWithFlashcards.has(tag.id));
  }, [bookHighlightTags, allFlashcardsWithContext]);

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

  // Chapters for ChapterNav (needs highlights array for count display)
  const navChapters = flashcardChapters.map((ch) => ({
    id: ch.id,
    name: ch.name,
    highlights: ch.flashcards as unknown as Highlight[],
  }));

  return (
    <>
      {/* Mobile Layout */}
      {!isDesktop && (
        <MobileFlashcardsContent
          searchText={searchText}
          onSearch={handleSearch}
          isReversed={isReversed}
          onToggleReverse={() => setIsReversed(!isReversed)}
          chapters={flashcardChapters}
          bookId={book.id}
          emptyMessage={emptyMessage}
          onEditFlashcard={setEditingFlashcard}
        />
      )}

      {/* Desktop Layout */}
      {isDesktop && (
        <DesktopFlashcardsContent
          book={book}
          tags={tagsWithFlashcards}
          selectedTagId={selectedTagId}
          onTagClick={handleTagClick}
          searchText={searchText}
          onSearch={handleSearch}
          isReversed={isReversed}
          onToggleReverse={() => setIsReversed(!isReversed)}
          chapters={flashcardChapters}
          navChapters={navChapters}
          bookId={book.id}
          emptyMessage={emptyMessage}
          onEditFlashcard={setEditingFlashcard}
          onChapterClick={handleChapterClick}
        />
      )}

      {/* Flashcard Edit Dialog */}
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

// Mobile content component
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

// Desktop content component
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
  navChapters: { id: number | string; name: string; highlights: Highlight[] }[];
  bookId: number;
  emptyMessage: string;
  onEditFlashcard: (flashcard: FlashcardWithContext) => void;
  onChapterClick: (chapterId: number | string) => void;
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
    {/* Left Column - Tags (filtered to those with flashcards) */}
    <HighlightTags
      tags={tags}
      tagGroups={book.highlight_tag_groups || []}
      bookId={book.id}
      selectedTag={selectedTagId}
      onTagClick={onTagClick}
      hideEmptyGroups
    />

    {/* Middle Column - Search + Content */}
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

    {/* Right Column - Chapters only (no bookmarks for flashcards) */}
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <ChapterNav chapters={navChapters} onChapterClick={onChapterClick} />
    </Box>
  </ThreeColumnLayout>
);

// Export hook for getting flashcard data needed by MobileNavigation
// eslint-disable-next-line react-refresh/only-export-components
export const useFlashcardsTabData = (book: BookDetails) => {
  const { tagId: urlTagId } = useSearch({ from: '/book/$bookId' });
  const selectedTagId = urlTagId;

  const bookChapters = book.chapters;
  const bookHighlightTags = book.highlight_tags;

  const allFlashcardsWithContext = useMemo((): FlashcardWithContext[] => {
    if (!bookChapters) return [];

    return flatMap(bookChapters, (chapter: ChapterWithHighlights) =>
      flatMap(chapter.highlights || [], (highlight: Highlight) =>
        (highlight.flashcards || []).map((flashcard: Flashcard) => ({
          ...flashcard,
          highlightText: highlight.text,
          chapterName: chapter.name || 'Unknown Chapter',
          chapterId: chapter.id,
          highlightTags: highlight.highlight_tags,
        }))
      )
    );
  }, [bookChapters]);

  const filteredFlashcards = useMemo((): FlashcardWithContext[] => {
    if (!selectedTagId) return allFlashcardsWithContext;
    return allFlashcardsWithContext.filter((fc) =>
      fc.highlightTags?.some((tag) => tag.id === selectedTagId)
    );
  }, [allFlashcardsWithContext, selectedTagId]);

  const flashcardChapters = useMemo((): FlashcardChapterData[] => {
    const grouped: Record<number, FlashcardWithContext[]> = {};
    for (const fc of filteredFlashcards) {
      if (fc.chapterId) {
        if (!grouped[fc.chapterId]) {
          grouped[fc.chapterId] = [];
        }
        grouped[fc.chapterId].push(fc);
      }
    }

    return Object.entries(grouped).map(([chapterId, flashcards]) => ({
      id: Number(chapterId),
      name: flashcards[0]?.chapterName || 'Unknown Chapter',
      flashcards,
    }));
  }, [filteredFlashcards]);

  const tagsWithFlashcards = useMemo(() => {
    if (!bookHighlightTags) return [];

    const tagIdsWithFlashcards = new Set<number>();
    for (const fc of allFlashcardsWithContext) {
      fc.highlightTags?.forEach((tag) => tagIdsWithFlashcards.add(tag.id));
    }

    return bookHighlightTags.filter((tag) => tagIdsWithFlashcards.has(tag.id));
  }, [bookHighlightTags, allFlashcardsWithContext]);

  const navChapters = flashcardChapters.map((ch) => ({
    id: ch.id,
    name: ch.name,
    highlights: ch.flashcards as unknown as Highlight[],
  }));

  return {
    chapters: navChapters,
    tags: tagsWithFlashcards,
    selectedTagId,
  };
};

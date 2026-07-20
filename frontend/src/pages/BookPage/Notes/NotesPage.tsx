import type { GetNotesForBookApiV1BooksBookIdNotesGetParams } from '@/api/generated/model';
import { useGetNotesForBookApiV1BooksBookIdNotesGet } from '@/api/generated/notes/notes.ts';
import { CardList } from '@/components/CardList.tsx';
import { EmptyStateText } from '@/components/EmptyStateText.tsx';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { useBookTabFilters } from '@/pages/BookPage/common/useBookTabFilters.ts';
import { AddIcon } from '@/theme/Icons.tsx';
import { Alert, Box, Button, Divider, ToggleButton, ToggleButtonGroup } from '@mui/material';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useState } from 'react';
import { createPortal } from 'react-dom';

import { FilterFab } from '../common/FilterFab.tsx';
import { FilterDrawer, type FilterTab } from '../navigation/FilterDrawer.tsx';
import { TagsList } from '../navigation/TagsList/TagsList.tsx';
import { NoteCard } from './NoteCard';
import { NoteModals } from './NoteModals';
import { useNoteModals } from './hooks/useNoteModals';
import { NOTE_KIND_LABELS, NOTE_KINDS, type NoteKindValue } from './noteKinds';

interface NoteKindFilterProps {
  value: NoteKindValue | null;
  onChange: (value: NoteKindValue | null) => void;
}

const NoteKindFilter = ({ value, onChange }: NoteKindFilterProps) => (
  <ToggleButtonGroup
    size="small"
    exclusive
    value={value}
    onChange={(_, next: NoteKindValue | null) => onChange(next)}
  >
    {NOTE_KINDS.map((kind) => (
      <ToggleButton key={kind} value={kind}>
        {NOTE_KIND_LABELS[kind]}
      </ToggleButton>
    ))}
  </ToggleButtonGroup>
);

export const NotesPage = () => {
  const { book, isDesktop, leftSidebarEl, fabContainerEl } = useBookPage();
  const navigate = useNavigate({ from: '/book/$bookId/notes' });
  const { kind, chapterId } = useSearch({ from: '/book/$bookId/notes' });

  const { selectedTagId, handleTagClick } = useBookTabFilters('/book/$bookId/notes');
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);

  const params: GetNotesForBookApiV1BooksBookIdNotesGetParams = {
    kind: (kind as NoteKindValue | undefined) ?? undefined,
    chapter_id: chapterId,
    tag_id: selectedTagId,
  };
  const { data, isLoading, isError } = useGetNotesForBookApiV1BooksBookIdNotesGet(book.id, params);
  // NOTE: the orval axios mutator unwraps the response (`.then(({ data }) => data)`),
  // so the generated GET hook's `data` is the payload itself, not an AxiosResponse.
  const notes = data?.items ?? [];
  const noteModals = useNoteModals({ allNotes: notes });

  const handleKindFilter = (value: NoteKindValue | null) => {
    void navigate({ search: (prev) => ({ ...prev, kind: value ?? undefined }) });
  };

  const filterTabs: FilterTab[] = [
    {
      label: 'Tags',
      content: (
        <TagsList
          tags={book.tags}
          tagGroups={book.tag_groups}
          bookId={book.id}
          selectedTag={selectedTagId}
          onTagClick={(id) => {
            handleTagClick(id);
            setFilterDrawerOpen(false);
          }}
          hideTitle
          hideEmptyGroups
        />
      ),
    },
  ];

  return (
    <Box>
      {isDesktop &&
        leftSidebarEl &&
        createPortal(
          <>
            <Divider sx={{ mb: 4 }} />
            <TagsList
              tags={book.tags}
              tagGroups={book.tag_groups}
              bookId={book.id}
              selectedTag={selectedTagId}
              onTagClick={handleTagClick}
              hideEmptyGroups
            />
          </>,
          leftSidebarEl
        )}

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <NoteKindFilter
          value={(kind as NoteKindValue | undefined) ?? null}
          onChange={handleKindFilter}
        />
        <Box sx={{ flexGrow: 1 }} />
        <Button variant="contained" startIcon={<AddIcon />} onClick={noteModals.openCreate}>
          New note
        </Button>
      </Box>

      {isLoading && <Spinner />}
      {isError && <Alert severity="error">Failed to load notes.</Alert>}
      {!isLoading && !isError && notes.length === 0 && (
        <EmptyStateText>
          {selectedTagId
            ? 'No notes found with the selected tag.'
            : 'No notes yet. Create notes about characters, terms, and concepts as you read.'}
        </EmptyStateText>
      )}

      <CardList>
        {notes.map((note) => (
          <li key={note.id}>
            <NoteCard note={note} onClick={() => noteModals.openView(note)} />
          </li>
        ))}
      </CardList>

      {!isDesktop &&
        fabContainerEl &&
        createPortal(
          <FilterFab filterEnabled={!!selectedTagId} onClick={() => setFilterDrawerOpen(true)} />,
          fabContainerEl
        )}
      {!isDesktop && (
        <FilterDrawer
          open={filterDrawerOpen}
          onClose={() => setFilterDrawerOpen(false)}
          tabs={filterTabs}
        />
      )}

      <NoteModals controller={noteModals} />
    </Box>
  );
};

import type { GetNotesForBookApiV1BooksBookIdNotesGetParams } from '@/api/generated/model';
import { useGetNotesForBookApiV1BooksBookIdNotesGet } from '@/api/generated/notes/notes.ts';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { AddIcon } from '@/theme/Icons.tsx';
import {
  Box,
  Button,
  Divider,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

import { FilterFab } from '../common/FilterFab.tsx';
import { FilterDrawer, type FilterTab } from '../navigation/FilterDrawer.tsx';
import { TagsList } from '../navigation/TagsList.tsx';
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
  const { kind, chapterId, tagId } = useSearch({ from: '/book/$bookId/notes' });

  const [selectedTagId, setSelectedTagId] = useState<number | undefined>(tagId);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);

  useEffect(() => {
    setSelectedTagId(tagId);
  }, [tagId]);

  const params: GetNotesForBookApiV1BooksBookIdNotesGetParams = {
    kind: (kind as NoteKindValue | undefined) ?? undefined,
    chapter_id: chapterId,
    tag_id: selectedTagId,
  };
  const { data, isLoading, isError } = useGetNotesForBookApiV1BooksBookIdNotesGet(book.id, params);
  const noteModals = useNoteModals();

  const handleKindFilter = (value: NoteKindValue | null) => {
    void navigate({ search: (prev) => ({ ...prev, kind: value ?? undefined }) });
  };

  const handleTagClick = (newTagId: number | null) => {
    setSelectedTagId(newTagId || undefined);
    void navigate({
      search: (prev) => ({ ...prev, tagId: newTagId || undefined }),
      replace: true,
    });
  };

  // NOTE: the orval axios mutator unwraps the response (`.then(({ data }) => data)`),
  // so the generated GET hook's `data` is the payload itself, not an AxiosResponse.
  const notes = data?.notes ?? [];

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
      {isError && <Typography color="error">Failed to load notes.</Typography>}
      {!isLoading && !isError && notes.length === 0 && (
        <Typography color="text.secondary">
          {selectedTagId
            ? 'No notes found with the selected tag.'
            : 'No notes yet. Create notes about characters, terms, and concepts as you read.'}
        </Typography>
      )}

      <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
        {notes.map((note) => (
          <li key={note.id}>
            <NoteCard note={note} onClick={() => noteModals.openView(note)} />
          </li>
        ))}
      </Stack>

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

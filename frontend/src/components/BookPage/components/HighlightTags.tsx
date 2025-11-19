import { useUpdateHighlightTagApiV1BookBookIdHighlightTagTagIdPost } from '@/api/generated/books/books';
import { HighlightTagGroupInBook, HighlightTagInBook } from '@/api/generated/model';
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  MouseSensor,
  TouchSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import {
  Close as CloseIcon,
  Settings as SettingsIcon,
  LocalOffer as TagIcon,
} from '@mui/icons-material';
import { Box, Chip, IconButton, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { motion } from 'motion/react';
import { useState } from 'react';
import { HighlightTagsModal } from './HighlightTagsModal';

interface HighlightTagsProps {
  tags: HighlightTagInBook[];
  tagGroups: HighlightTagGroupInBook[];
  bookId: number;
  selectedTag?: number | null;
  onTagClick: (tagId: number | null) => void;
}

interface DraggableTagProps {
  tag: HighlightTagInBook;
  selectedTag: number | null | undefined;
  onTagClick: (tagId: number | null) => void;
  isDragOverlay?: boolean;
}

const DraggableTag = ({ tag, selectedTag, onTagClick, isDragOverlay }: DraggableTagProps) => {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `tag-${tag.id}`,
    data: { tag },
  });

  const style =
    transform && !isDragging
      ? {
          transform: CSS.Translate.toString(transform),
          zIndex: 1000,
        }
      : undefined;

  return (
    <Box
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      sx={{
        opacity: isDragging && !isDragOverlay ? 0.3 : 1,
        cursor: isDragging ? 'grabbing' : 'grab',
      }}
    >
      <Chip
        label={tag.name}
        size="small"
        variant={selectedTag === tag.id ? 'filled' : 'outlined'}
        color={selectedTag === tag.id ? 'primary' : 'default'}
        onClick={(e) => {
          e.stopPropagation();
          onTagClick(selectedTag === tag.id ? null : tag.id);
        }}
        sx={{
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          py: 0.25,
          px: 0.5,
          borderColor: selectedTag === tag.id ? undefined : 'divider',
          '&:hover': {
            bgcolor: selectedTag === tag.id ? 'primary.dark' : 'action.hover',
            borderColor: selectedTag === tag.id ? undefined : 'secondary.light',
            transform: 'translateY(-1px)',
          },
        }}
      />
    </Box>
  );
};

interface DroppableGroupProps {
  id: string;
  children: React.ReactNode;
  isEmpty?: boolean;
  emptyHeight?: number;
}

const DroppableGroup = ({ id, children, isEmpty, emptyHeight }: DroppableGroupProps) => {
  const { isOver, setNodeRef } = useDroppable({
    id,
  });

  return (
    <motion.div
      ref={setNodeRef}
      animate={{
        backgroundColor: isOver ? 'rgba(104, 90, 75, 0.08)' : 'rgba(104, 90, 75, 0)',
        borderColor: isOver
          ? 'rgba(104, 90, 75, 0.4)'
          : isEmpty
            ? 'rgba(0, 0, 0, 0.12)'
            : 'rgba(0, 0, 0, 0)',
      }}
      transition={{ duration: 0.2 }}
      style={{
        border: isEmpty ? '1px dashed' : isOver ? '2px solid' : 'none',
        borderRadius: 4,
        padding: isEmpty ? 16 : isOver ? 8 : 0,
        minHeight: isEmpty ? emptyHeight || 60 : 'auto',
      }}
    >
      {children}
    </motion.div>
  );
};

const EmptyGroupPlaceholder = ({ message }: { message: string }) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <Typography
      variant="body2"
      color="text.secondary"
      sx={{ textAlign: 'center', fontSize: '0.813rem' }}
    >
      {message}
    </Typography>
  </Box>
);

const HighlightTagsHeading = ({
  selectedTag,
  onTagClick,
  onManageClick,
}: {
  onTagClick: HighlightTagsProps['onTagClick'];
  selectedTag: HighlightTagsProps['selectedTag'];
  onManageClick: () => void;
}) => (
  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <TagIcon sx={{ fontSize: 20, color: 'primary.main' }} />
      <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
        Tags
      </Typography>
    </Box>
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <IconButton
        size="small"
        onClick={onManageClick}
        title="Manage tag groups"
        sx={{ color: 'text.secondary' }}
      >
        <SettingsIcon fontSize="small" />
      </IconButton>
      <IconButton
        size="small"
        onClick={() => onTagClick(null)}
        title="Clear filter"
        sx={{
          visibility: selectedTag ? 'visible' : 'hidden',
        }}
      >
        <CloseIcon fontSize="small" />
      </IconButton>
    </Box>
  </Box>
);

export const HighlightTags = ({
  tags,
  tagGroups,
  bookId,
  selectedTag,
  onTagClick,
}: HighlightTagsProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTag, setActiveTag] = useState<HighlightTagInBook | null>(null);
  const [movingTagId, setMovingTagId] = useState<number | null>(null);
  const queryClient = useQueryClient();

  // Set up sensors for drag and drop - separate mouse and touch for better mobile support
  const sensors = useSensors(
    useSensor(MouseSensor, {
      activationConstraint: {
        distance: 8, // Require 8px of movement before drag starts
      },
    }),
    useSensor(TouchSensor, {
      activationConstraint: {
        delay: 200, // 200ms delay before drag starts on touch
        tolerance: 5, // Allow 5px of movement during the delay
      },
    })
  );

  // Update tag mutation with optimistic updates
  const updateTagMutation = useUpdateHighlightTagApiV1BookBookIdHighlightTagTagIdPost({
    mutation: {
      onMutate: async (variables) => {
        // Cancel any outgoing refetches
        await queryClient.cancelQueries({
          queryKey: [`/api/v1/book/${bookId}`],
        });

        // Snapshot the previous value
        const previousBook = queryClient.getQueryData([`/api/v1/book/${bookId}`]);

        // Optimistically update the cache
        queryClient.setQueryData([`/api/v1/book/${bookId}`], (old: unknown) => {
          if (!old || typeof old !== 'object') return old;
          const bookData = old as { highlight_tags: HighlightTagInBook[] };

          return {
            ...bookData,
            highlight_tags: bookData.highlight_tags.map((tag: HighlightTagInBook) =>
              tag.id === variables.tagId
                ? { ...tag, tag_group_id: variables.data.tag_group_id }
                : tag
            ),
          };
        });

        // Return a context object with the snapshotted value
        return { previousBook };
      },
      onSuccess: (updatedTag) => {
        // Update cache with actual server response to prevent drift
        queryClient.setQueryData([`/api/v1/book/${bookId}`], (old: unknown) => {
          if (!old || typeof old !== 'object') return old;
          const bookData = old as { highlight_tags: HighlightTagInBook[] };

          return {
            ...bookData,
            highlight_tags: bookData.highlight_tags.map((tag: HighlightTagInBook) =>
              tag.id === updatedTag.id ? updatedTag : tag
            ),
          };
        });
      },
      onError: (error: unknown, _variables, context) => {
        // If the mutation fails, use the context to roll back
        if (context?.previousBook) {
          queryClient.setQueryData([`/api/v1/book/${bookId}`], context.previousBook);
        }
        console.error('Failed to update tag:', error);
      },
    },
  });

  // Sort tags alphabetically and filter out the tag being moved
  const sortedTags = [...tags]
    .filter((tag) => tag.id !== movingTagId)
    .sort((a, b) => a.name.localeCompare(b.name));

  // Group tags by tag_group_id
  const ungroupedTags = sortedTags.filter((tag) => !tag.tag_group_id);
  const groupedTags = tagGroups.map((group) => ({
    group,
    tags: sortedTags.filter((tag) => tag.tag_group_id === group.id),
  }));

  const handleDragStart = (event: DragStartEvent) => {
    const tag = event.active.data.current?.tag;
    if (tag) {
      setActiveTag(tag);
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTag(null);

    if (!over) return;

    const tag = active.data.current?.tag as HighlightTagInBook;
    const dropZoneId = over.id as string;

    // Parse the drop zone ID to get the group ID
    let newGroupId: number | null = null;
    if (dropZoneId.startsWith('group-')) {
      newGroupId = parseInt(dropZoneId.replace('group-', ''), 10);
    }
    // If dropZoneId === 'ungrouped', newGroupId remains null

    // Only update if the group has changed
    if (tag.tag_group_id !== newGroupId) {
      // Hide the tag during transition
      setMovingTagId(tag.id);

      try {
        await updateTagMutation.mutateAsync({
          bookId,
          tagId: tag.id,
          data: {
            tag_group_id: newGroupId,
          },
        });
      } catch (error) {
        console.error('Error updating tag group:', error);
      } finally {
        // Show the tag again after mutation completes
        setMovingTagId(null);
      }
    }
  };

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <Box
        sx={{
          position: 'sticky',
          top: 24,
        }}
      >
        <HighlightTagsHeading
          selectedTag={selectedTag}
          onTagClick={onTagClick}
          onManageClick={() => setIsModalOpen(true)}
        />

        {tags && tags.length > 0 ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Ungrouped tags - always present to avoid layout shift */}
            <motion.div
              initial={false}
              animate={{
                height:
                  ungroupedTags.length === 0 && activeTag === null && movingTagId === null
                    ? 0
                    : 'auto',
                marginBottom:
                  ungroupedTags.length === 0 && activeTag === null && movingTagId === null ? 0 : 16,
                opacity:
                  ungroupedTags.length === 0 && activeTag === null && movingTagId === null ? 0 : 1,
              }}
              transition={{ duration: 0.2 }}
              style={{ overflow: 'hidden' }}
            >
              <DroppableGroup id="ungrouped" isEmpty={ungroupedTags.length === 0} emptyHeight={30}>
                {ungroupedTags.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {ungroupedTags.map((tag) => (
                      <DraggableTag
                        key={tag.id}
                        tag={tag}
                        selectedTag={selectedTag}
                        onTagClick={onTagClick}
                      />
                    ))}
                  </Box>
                ) : (
                  <EmptyGroupPlaceholder message="Drop here to remove from groups" />
                )}
              </DroppableGroup>
            </motion.div>

            {/* Grouped tags */}
            {groupedTags.map(({ group, tags: groupTags }) => (
              <Box key={group.id} sx={{ mb: 1 }}>
                <Typography
                  variant="subtitle2"
                  sx={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: 'text.secondary',
                    mb: 1,
                  }}
                >
                  {group.name}
                </Typography>
                <DroppableGroup id={`group-${group.id}`} isEmpty={groupTags.length === 0}>
                  {groupTags.length > 0 ? (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {groupTags.map((tag) => (
                        <DraggableTag
                          key={tag.id}
                          tag={tag}
                          selectedTag={selectedTag}
                          onTagClick={onTagClick}
                        />
                      ))}
                    </Box>
                  ) : (
                    <EmptyGroupPlaceholder message="No tags in this group. Drag tags here." />
                  )}
                </DroppableGroup>
              </Box>
            ))}
          </Box>
        ) : (
          <Typography variant="body1" color="text.secondary">
            No tagged highlights.
          </Typography>
        )}
      </Box>

      <DragOverlay>
        {activeTag ? (
          <DraggableTag
            tag={activeTag}
            selectedTag={selectedTag}
            onTagClick={onTagClick}
            isDragOverlay
          />
        ) : null}
      </DragOverlay>

      <HighlightTagsModal
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        bookId={bookId}
        tagGroups={tagGroups}
      />
    </DndContext>
  );
};

import {
  getGetBookDetailsApiV1BooksBookIdGetQueryKey,
  useUpdateHighlightTagApiV1BooksBookIdHighlightTagTagIdPost,
} from '@/api/generated/books/books.ts';
import {
  useCreateOrUpdateTagGroupApiV1HighlightsTagGroupPost,
  useDeleteTagGroupApiV1HighlightsTagGroupTagGroupIdDelete,
} from '@/api/generated/highlights/highlights.ts';
import { HighlightTagGroupInBook, HighlightTagInBook } from '@/api/generated/model';
import { Collapsable } from '@/components/common/animations/Collapsable.tsx';
import { AddIcon, DeleteIcon, EditIcon, ExpandMoreIcon, TagIcon } from '@/components/common/Icons.tsx';
import { createAdaptiveHoverStyles, createAdaptiveTouchTarget } from '@/utils/adaptiveHover.ts';
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
  Box,
  Chip,
  ClickAwayListener,
  IconButton,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { sortBy } from 'lodash';
import { AnimatePresence, motion } from 'motion/react';
import { KeyboardEvent, useRef, useState } from 'react';

interface HighlightTagsProps {
  tags: HighlightTagInBook[];
  tagGroups: HighlightTagGroupInBook[];
  bookId: number;
  selectedTag?: number | null;
  onTagClick: (tagId: number | null) => void;
  hideTitle?: boolean;
  hideEmptyGroups?: boolean;
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
        borderRadius: 8,
        padding: isEmpty ? 12 : isOver ? 8 : 0,
        minHeight: isEmpty ? emptyHeight || 40 : 'auto',
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
      sx={{ textAlign: 'center', fontSize: '0.75rem', fontStyle: 'italic' }}
    >
      {message}
    </Typography>
  </Box>
);

interface TagGroupProps {
  group: HighlightTagGroupInBook;
  tags: HighlightTagInBook[];
  isCollapsed: boolean;
  isEditing: boolean;
  editValue: string;
  isProcessing: boolean;
  selectedTag: number | null | undefined;
  onToggleCollapse: () => void;
  onStartEdit: () => void;
  onEditChange: (value: string) => void;
  onEditSubmit: () => void;
  onEditCancel: () => void;
  onDelete: () => void;
  onTagClick: (tagId: number | null) => void;
}

const TagGroup = ({
  group,
  tags,
  isCollapsed,
  isEditing,
  editValue,
  isProcessing,
  selectedTag,
  onToggleCollapse,
  onStartEdit,
  onEditChange,
  onEditSubmit,
  onEditCancel,
  onDelete,
  onTagClick,
}: TagGroupProps) => {
  return (
    <Box
      sx={{
        p: 1.5,
        bgcolor: 'rgba(255, 255, 255, 0.6)',
        borderRadius: 1,
        border: '1px solid',
        borderColor: 'divider',
        transition: 'all 0.15s',
      }}
    >
      <TagGroupHeader
        group={group}
        tagCount={tags.length}
        isCollapsed={isCollapsed}
        isEditing={isEditing}
        editValue={editValue}
        onToggleCollapse={onToggleCollapse}
        onStartEdit={onStartEdit}
        onEditChange={onEditChange}
        onEditSubmit={onEditSubmit}
        onEditCancel={onEditCancel}
        onDelete={onDelete}
        isProcessing={isProcessing}
      />
      <Collapsable isExpanded={!isCollapsed}>
        <DroppableGroup id={`group-${group.id}`} isEmpty={tags.length === 0}>
          {tags.length > 0 ? (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
              {tags.map((tag) => (
                <DraggableTag
                  key={tag.id}
                  tag={tag}
                  selectedTag={selectedTag}
                  onTagClick={onTagClick}
                />
              ))}
            </Box>
          ) : (
            <EmptyGroupPlaceholder message="Drag tags here" />
          )}
        </DroppableGroup>
      </Collapsable>
    </Box>
  );
};

interface UngroupedTagsProps {
  tags: HighlightTagInBook[];
  selectedTag: number | null | undefined;
  activeTag: HighlightTagInBook | null;
  movingTagId: number | null;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onTagClick: (tagId: number | null) => void;
}

const UngroupedTags = ({
  tags,
  selectedTag,
  activeTag,
  movingTagId,
  isCollapsed,
  onToggleCollapse,
  onTagClick,
}: UngroupedTagsProps) => {
  const shouldHide = tags.length === 0 && activeTag === null && movingTagId === null;

  return (
    <motion.div
      initial={false}
      animate={{
        height: shouldHide ? 0 : 'auto',
        opacity: shouldHide ? 0 : 1,
      }}
      transition={{ duration: 0.2 }}
      style={{ overflow: 'hidden' }}
    >
      <Box
        sx={{
          p: 1.5,
          bgcolor: 'rgba(255, 255, 255, 0.4)',
          borderRadius: 1,
          border: '1px dashed',
          borderColor: 'divider',
        }}
      >
        <Box sx={{ mb: isCollapsed ? 0 : 1 }}>
          <TagGroupTitle
            title="Ungrouped"
            count={tags.length}
            isCollapsed={isCollapsed}
            onToggleCollapse={onToggleCollapse}
          />
        </Box>
        <Collapsable isExpanded={!isCollapsed}>
          <DroppableGroup id="ungrouped" isEmpty={tags.length === 0} emptyHeight={30}>
            {tags.length > 0 ? (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                {tags.map((tag) => (
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
        </Collapsable>
      </Box>
    </motion.div>
  );
};

interface AddGroupFormProps {
  isVisible: boolean;
  groupName: string;
  isProcessing: boolean;
  onGroupNameChange: (name: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
}

const AddGroupForm = ({
  isVisible,
  groupName,
  isProcessing,
  onGroupNameChange,
  onSubmit,
  onCancel,
}: AddGroupFormProps) => {
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onSubmit();
    } else if (e.key === 'Escape') {
      onCancel();
    }
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.15 }}
          style={{ overflow: 'hidden' }}
        >
          <Box
            sx={{
              mb: 2,
              p: 1.5,
              bgcolor: 'action.hover',
              borderRadius: 1,
              border: '1px dashed',
              borderColor: 'divider',
            }}
          >
            <ClickAwayListener onClickAway={onSubmit}>
              <TextField
                value={groupName}
                onChange={(e) => onGroupNameChange(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Group name..."
                size="small"
                autoFocus
                disabled={isProcessing}
                fullWidth
                sx={{
                  mb: 1,
                  '& .MuiInputBase-input': {
                    py: 0.75,
                    px: 1.5,
                    fontSize: '0.813rem',
                  },
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1.5,
                    bgcolor: 'background.paper',
                  },
                }}
              />
            </ClickAwayListener>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Box
                component="button"
                onClick={onSubmit}
                disabled={isProcessing}
                sx={{
                  flex: 1,
                  py: 0.75,
                  px: 1.5,
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                  border: 'none',
                  borderRadius: 1.5,
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'primary.dark' },
                  '&:disabled': { opacity: 0.6, cursor: 'not-allowed' },
                }}
              >
                Add
              </Box>
              <Box
                component="button"
                onClick={onCancel}
                sx={{
                  flex: 1,
                  py: 0.75,
                  px: 1.5,
                  bgcolor: 'transparent',
                  color: 'text.secondary',
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1.5,
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'action.hover' },
                }}
              >
                Cancel
              </Box>
            </Box>
          </Box>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

interface TagGroupTitleProps {
  title: string;
  count: number;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

const TagGroupTitle = ({ title, count, isCollapsed, onToggleCollapse }: TagGroupTitleProps) => {
  return (
    <Box
      onClick={onToggleCollapse}
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 0.5,
        flex: 1,
        cursor: 'pointer',
      }}
    >
      <ExpandMoreIcon
        sx={{
          fontSize: 16,
          color: 'text.secondary',
          transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)',
          transition: 'transform 0.15s',
        }}
      />
      <Typography
        variant="subtitle2"
        sx={{
          fontSize: '0.75rem',
          fontWeight: 600,
          color: 'text.secondary',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        {title}
        <Typography
          component="span"
          sx={{
            fontSize: '0.7rem',
            fontWeight: 400,
            color: 'text.disabled',
            ml: 0.5,
          }}
        >
          ({count})
        </Typography>
      </Typography>
    </Box>
  );
};

interface TagGroupHeaderProps {
  group: HighlightTagGroupInBook;
  tagCount: number;
  isCollapsed: boolean;
  isEditing: boolean;
  editValue: string;
  onToggleCollapse: () => void;
  onStartEdit: () => void;
  onEditChange: (value: string) => void;
  onEditSubmit: () => void;
  onEditCancel: () => void;
  onDelete: () => void;
  isProcessing: boolean;
}

const TagGroupHeader = ({
  group,
  tagCount,
  isCollapsed,
  isEditing,
  editValue,
  onToggleCollapse,
  onStartEdit,
  onEditChange,
  onEditSubmit,
  onEditCancel,
  onDelete,
  isProcessing,
}: TagGroupHeaderProps) => {
  const inputRef = useRef<HTMLInputElement>(null);

  const adaptiveStyles = createAdaptiveHoverStyles({
    actionsClassName: 'group-actions',
    transitionDuration: 0.15,
  });
  const touchTarget = createAdaptiveTouchTarget();

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onEditSubmit();
    } else if (e.key === 'Escape') {
      onEditCancel();
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        mb: isCollapsed ? 0 : 1,
        cursor: 'pointer',
        ...adaptiveStyles.container,
      }}
    >
      {isEditing ? (
        <ClickAwayListener onClickAway={onEditSubmit}>
          <TextField
            inputRef={inputRef}
            value={editValue}
            onChange={(e) => onEditChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={onEditSubmit}
            size="small"
            autoFocus
            disabled={isProcessing}
            sx={{
              flex: 1,
              mr: 1,
              '& .MuiInputBase-input': {
                py: 0.5,
                px: 1,
                fontSize: '0.75rem',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              },
              '& .MuiOutlinedInput-root': {
                borderRadius: 1,
              },
            }}
          />
        </ClickAwayListener>
      ) : (
        <TagGroupTitle
          title={group.name}
          count={tagCount}
          isCollapsed={isCollapsed}
          onToggleCollapse={onToggleCollapse}
        />
      )}
      {!isEditing && (
        <Box
          className="group-actions"
          sx={{
            ...adaptiveStyles.actions,
            gap: 0.25,
          }}
        >
          <Tooltip title="Rename group">
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onStartEdit();
              }}
              sx={{ ...touchTarget, color: 'text.disabled' }}
            >
              <EditIcon sx={{ fontSize: 14 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete group">
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              disabled={isProcessing}
              sx={{ ...touchTarget, color: 'text.disabled' }}
            >
              <DeleteIcon sx={{ fontSize: 14 }} />
            </IconButton>
          </Tooltip>
        </Box>
      )}
    </Box>
  );
};

export const HighlightTagsList = ({
  tags,
  tagGroups,
  bookId,
  selectedTag,
  onTagClick,
  hideTitle,
  hideEmptyGroups,
}: HighlightTagsProps) => {
  const [collapsedGroups, setCollapsedGroups] = useState<Record<number, boolean>>({});
  const [ungroupedCollapsed, setUngroupedCollapsed] = useState(false);
  const [editingGroupId, setEditingGroupId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState('');
  const [showAddGroup, setShowAddGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [activeTag, setActiveTag] = useState<HighlightTagInBook | null>(null);
  const [movingTagId, setMovingTagId] = useState<number | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const queryClient = useQueryClient();

  // Set up sensors for drag and drop
  const sensors = useSensors(
    useSensor(MouseSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(TouchSensor, {
      activationConstraint: {
        delay: 200,
        tolerance: 5,
      },
    })
  );

  // Mutations
  const updateTagMutation = useUpdateHighlightTagApiV1BooksBookIdHighlightTagTagIdPost({
    mutation: {
      onMutate: async (variables) => {
        await queryClient.cancelQueries({
          queryKey: [`/api/v1/books/${bookId}`],
        });
        const previousBook = queryClient.getQueryData([`/api/v1/books/${bookId}`]);
        queryClient.setQueryData([`/api/v1/books/${bookId}`], (old: unknown) => {
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
        return { previousBook };
      },
      onSuccess: (updatedTag) => {
        queryClient.setQueryData([`/api/v1/books/${bookId}`], (old: unknown) => {
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
        if (context?.previousBook) {
          queryClient.setQueryData([`/api/v1/books/${bookId}`], context.previousBook);
        }
        console.error('Failed to update tag:', error);
      },
    },
  });

  const createOrUpdateGroupMutation = useCreateOrUpdateTagGroupApiV1HighlightsTagGroupPost({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
      },
      onError: (error: unknown) => {
        console.error('Failed to create/update tag group:', error);
      },
    },
  });

  const deleteGroupMutation = useDeleteTagGroupApiV1HighlightsTagGroupTagGroupIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetBookDetailsApiV1BooksBookIdGetQueryKey(bookId),
        });
      },
      onError: (error: unknown) => {
        console.error('Failed to delete tag group:', error);
      },
    },
  });

  // Sort tags alphabetically and filter out the tag being moved
  const sortedTags = [...tags]
    .filter((tag) => tag.id !== movingTagId)
    .sort((a, b) => a.name.localeCompare(b.name));

  // Group tags by tag_group_id
  const ungroupedTags = sortedTags.filter((tag) => !tag.tag_group_id);
  const groupedTags = sortBy(
    tagGroups.map((group) => ({
      group,
      tags: sortedTags.filter((tag) => tag.tag_group_id === group.id),
    })),
    'group.name'
  );

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

    let newGroupId: number | null = null;
    if (dropZoneId.startsWith('group-')) {
      newGroupId = parseInt(dropZoneId.replace('group-', ''), 10);
    }

    if (tag.tag_group_id !== newGroupId) {
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
        setMovingTagId(null);
      }
    }
  };

  const handleToggleCollapse = (groupId: number) => {
    setCollapsedGroups((prev) => ({
      ...prev,
      [groupId]: !prev[groupId],
    }));
  };

  const handleToggleUngroupedCollapse = () => {
    setUngroupedCollapsed((prev) => !prev);
  };

  const handleStartEdit = (group: HighlightTagGroupInBook) => {
    setEditingGroupId(group.id);
    setEditValue(group.name);
  };

  const handleEditSubmit = async () => {
    if (!editingGroupId || !editValue.trim()) {
      setEditingGroupId(null);
      setEditValue('');
      return;
    }

    const originalGroup = tagGroups.find((g) => g.id === editingGroupId);
    if (originalGroup && originalGroup.name === editValue.trim()) {
      setEditingGroupId(null);
      setEditValue('');
      return;
    }

    setIsProcessing(true);
    try {
      await createOrUpdateGroupMutation.mutateAsync({
        data: {
          book_id: bookId,
          id: editingGroupId,
          name: editValue.trim(),
        },
      });
    } finally {
      setIsProcessing(false);
      setEditingGroupId(null);
      setEditValue('');
    }
  };

  const handleEditCancel = () => {
    setEditingGroupId(null);
    setEditValue('');
  };

  const handleDeleteGroup = async (groupId: number) => {
    setIsProcessing(true);
    try {
      await deleteGroupMutation.mutateAsync({
        tagGroupId: groupId,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAddGroup = async () => {
    if (!newGroupName.trim()) {
      setShowAddGroup(false);
      setNewGroupName('');
      return;
    }

    setIsProcessing(true);
    try {
      await createOrUpdateGroupMutation.mutateAsync({
        data: {
          book_id: bookId,
          name: newGroupName.trim(),
        },
      });
      setNewGroupName('');
      setShowAddGroup(false);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <Box>
        {/* Header */}
        {!hideTitle && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              mb: 2,
              pb: 1.5,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TagIcon sx={{ fontSize: 18, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
                Tags
              </Typography>
            </Box>
            <Tooltip title="Add new group">
              <IconButton
                size="small"
                onClick={() => setShowAddGroup(true)}
                sx={{ color: 'text.secondary', padding: 0.5 }}
              >
                <AddIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </Tooltip>
          </Box>
        )}

        {/* Add New Group Form */}
        <AddGroupForm
          isVisible={showAddGroup}
          groupName={newGroupName}
          isProcessing={isProcessing}
          onGroupNameChange={setNewGroupName}
          onSubmit={() => void handleAddGroup()}
          onCancel={() => {
            setShowAddGroup(false);
            setNewGroupName('');
          }}
        />

        {/* Tag Groups Content */}
        {tags && tags.length > 0 ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Grouped tags */}
            {groupedTags.map(({ group, tags: groupTags }) =>
              hideEmptyGroups && groupTags.length === 0 ? null : (
                <TagGroup
                  key={group.id}
                  group={group}
                  tags={groupTags}
                  isCollapsed={!!collapsedGroups[group.id]}
                  isEditing={editingGroupId === group.id}
                  editValue={editValue}
                  isProcessing={isProcessing}
                  selectedTag={selectedTag}
                  onToggleCollapse={() => handleToggleCollapse(group.id)}
                  onStartEdit={() => handleStartEdit(group)}
                  onEditChange={setEditValue}
                  onEditSubmit={() => void handleEditSubmit()}
                  onEditCancel={handleEditCancel}
                  onDelete={() => void handleDeleteGroup(group.id)}
                  onTagClick={onTagClick}
                />
              )
            )}

            {/* Ungrouped tags */}
            {hideEmptyGroups && ungroupedTags.length === 0 ? null : (
              <UngroupedTags
                tags={ungroupedTags}
                selectedTag={selectedTag}
                activeTag={activeTag}
                movingTagId={movingTagId}
                isCollapsed={ungroupedCollapsed}
                onToggleCollapse={handleToggleUngroupedCollapse}
                onTagClick={onTagClick}
              />
            )}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.813rem' }}>
            No tagged highlights yet.
          </Typography>
        )}

        {/* Tip */}
        {tags && tags.length > 0 && (
          <Box
            sx={{
              mt: 2,
              p: 1.5,
              bgcolor: 'action.hover',
              borderRadius: 1,
              fontSize: '0.7rem',
              color: 'text.secondary',
              lineHeight: 1.5,
            }}
          >
            <strong>Tip:</strong> Drag tags between groups to organize them. Click the pencil icon
            to rename a group.
          </Box>
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
    </DndContext>
  );
};

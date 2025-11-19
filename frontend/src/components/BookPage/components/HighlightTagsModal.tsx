import {
  useCreateOrUpdateTagGroupApiV1HighlightsTagGroupPost,
  useDeleteTagGroupApiV1HighlightsTagGroupTagGroupIdDelete,
} from '@/api/generated/highlights/highlights';
import type { HighlightTagGroupInBook } from '@/api/generated/model';
import { CommonDialog } from '@/components/common/CommonDialog';
import { Delete as DeleteIcon } from '@mui/icons-material';
import { Box, Button, IconButton, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Controller, useFieldArray, useForm } from 'react-hook-form';

interface TagGroupFormData {
  tagGroups: Array<{
    groupId?: number; // Database ID (renamed from 'id' to avoid conflict with RHF's internal id)
    name: string;
    isNew?: boolean;
  }>;
}

interface HighlightTagsModalProps {
  open: boolean;
  onClose: () => void;
  bookId: number;
  tagGroups: HighlightTagGroupInBook[];
}

const extractErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    return response?.data?.detail || 'Unknown error';
  }
  return 'Unknown error';
};

export const HighlightTagsModal = ({
  open,
  onClose,
  bookId,
  tagGroups,
}: HighlightTagsModalProps) => {
  const queryClient = useQueryClient();
  const [isProcessing, setIsProcessing] = useState(false);

  const { control, reset, watch } = useForm<TagGroupFormData>({
    defaultValues: {
      tagGroups: [],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'tagGroups',
  });

  // Initialize form with existing tag groups and add an empty field
  useEffect(() => {
    if (open) {
      const existingGroups = tagGroups.map((group) => ({
        groupId: group.id,
        name: group.name,
        isNew: false,
      }));
      reset({
        tagGroups: [...existingGroups, { name: '', isNew: true }],
      });
    }
  }, [tagGroups, open, reset]);

  const createTagGroupMutation = useCreateOrUpdateTagGroupApiV1HighlightsTagGroupPost({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: [`/api/v1/book/${bookId}`],
        });
      },
      onError: (error: unknown) => {
        console.error('Failed to create/update tag group:', error);
        alert(`Failed to save tag group: ${extractErrorMessage(error)}`);
      },
    },
  });

  const deleteTagGroupMutation = useDeleteTagGroupApiV1HighlightsTagGroupTagGroupIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: [`/api/v1/book/${bookId}`],
        });
      },
      onError: (error: unknown) => {
        console.error('Failed to delete tag group:', error);
        alert(`Failed to delete tag group: ${extractErrorMessage(error)}`);
      },
    },
  });

  const handleFieldBlur = async (index: number, value: string) => {
    const field = fields[index];
    const trimmedValue = value.trim();

    // Skip if empty
    if (!trimmedValue) {
      // If it's a new empty field and not the last one, remove it
      if (field.isNew && index !== fields.length - 1) {
        remove(index);
      }
      return;
    }

    // Skip if value hasn't changed for existing groups
    if (!field.isNew) {
      const originalGroup = tagGroups.find((g) => g.id === field.groupId);
      if (originalGroup && originalGroup.name === trimmedValue) {
        return;
      }
    }

    setIsProcessing(true);
    try {
      // Create or update tag group
      // Only include id if it exists (not undefined)
      const requestData: {
        book_id: number;
        name: string;
        id?: number | null;
      } = {
        book_id: bookId,
        name: trimmedValue,
      };

      if (field.groupId !== undefined) {
        requestData.id = field.groupId;
      }

      await createTagGroupMutation.mutateAsync({
        data: requestData,
      });

      // If this was the last "new" field, add another empty one
      if (field.isNew && index === fields.length - 1) {
        append({ name: '', isNew: true });
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelete = async (index: number) => {
    const field = fields[index];

    // If it's a new unsaved field, just remove it from the form
    if (field.isNew) {
      remove(index);
      return;
    }

    // Confirm deletion
    if (!confirm(`Are you sure you want to delete the tag group "${field.name}"?`)) {
      return;
    }

    setIsProcessing(true);
    try {
      if (field.groupId) {
        await deleteTagGroupMutation.mutateAsync({
          tagGroupId: field.groupId,
        });
        remove(index);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const watchedFields = watch('tagGroups');

  return (
    <CommonDialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      isLoading={isProcessing}
      title="Manage Tag Groups"
      footerActions={
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
          <Button onClick={onClose} disabled={isProcessing}>
            Close
          </Button>
        </Box>
      }
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Tag groups help you organize your highlight tags by theme or category.
        </Typography>

        {fields.map((field, index) => (
          <Box key={field.id} sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Controller
              name={`tagGroups.${index}.name`}
              control={control}
              render={({ field: { onChange, value } }) => (
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Enter tag group name..."
                  value={value}
                  onChange={onChange}
                  onBlur={() => void handleFieldBlur(index, value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      (e.target as HTMLInputElement).blur();
                    }
                  }}
                  disabled={isProcessing}
                  sx={{ flex: 1 }}
                />
              )}
            />
            {/* Show delete button for existing groups and new groups with text (but not the last empty field) */}
            {(!field.isNew || (field.isNew && watchedFields[index]?.name.trim())) && (
              <IconButton
                size="small"
                onClick={() => void handleDelete(index)}
                disabled={isProcessing}
                color="error"
                aria-label={`Delete ${field.name || 'tag group'}`}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            )}
          </Box>
        ))}

        {fields.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
            No tag groups yet. Start typing to create one!
          </Typography>
        )}
      </Box>
    </CommonDialog>
  );
};

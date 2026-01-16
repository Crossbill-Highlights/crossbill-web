import { Autocomplete, TextField } from '@mui/material';
import { Control, Controller, FieldValues, Path } from 'react-hook-form';

interface TagInputProps<T extends FieldValues> {
  control: Control<T>;
  name: Path<T>;
  label?: string;
  placeholder?: string;
  helperText?: string;
  disabled?: boolean;
  availableTags?: string[];
}

export const TagInput = <T extends FieldValues>({
  control,
  name,
  label = 'Tags',
  placeholder = 'Add tags...',
  helperText = 'Press Enter to add a tag',
  disabled = false,
  availableTags = [],
}: TagInputProps<T>) => {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <Autocomplete
          multiple
          freeSolo
          options={availableTags}
          value={field.value}
          onChange={(_, newValue) => {
            field.onChange(newValue);
          }}
          onBlur={field.onBlur}
          renderInput={(params) => (
            <TextField
              {...params}
              label={label}
              placeholder={placeholder}
              helperText={helperText}
              disabled={disabled}
            />
          )}
          slotProps={{
            chip: {
              disabled: disabled,
            },
          }}
          disabled={disabled}
        />
      )}
    />
  );
};

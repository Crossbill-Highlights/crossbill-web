import { TagInBook } from '@/api/generated/model';
import { BaseTagInputProps, TagAutocomplete } from '@/components/inputs/TagInput';

export interface TagInputProps extends BaseTagInputProps {
  value: TagInBook[];
  onChange: (newTags: (TagInBook | string)[]) => void | Promise<void>;
  availableTags?: TagInBook[];
  isProcessing?: boolean;
}

export const TagInput = ({
  value,
  onChange,
  label = 'Tags',
  placeholder = 'Add tags...',
  helperText = 'Press Enter to add a tag, click X to remove',
  disabled = false,
  availableTags = [],
  isProcessing = false,
  chipAriaDescription = 'Selected tag, click to remove',
}: TagInputProps) => {
  const isDisabled = disabled || isProcessing;

  return (
    <TagAutocomplete
      value={value}
      onChange={onChange}
      options={availableTags}
      disabled={isDisabled}
      blurOnSelect={false}
      placeholder={placeholder}
      helperText={helperText}
      preventParentNavigation={true}
      chipAriaDescription={chipAriaDescription}
      getOptionLabel={(option) => (typeof option === 'string' ? option : option.name)}
      isOptionEqualToValue={(option, value) => option.id === value.id}
      label={label}
      showLabelAsTypography={true}
    />
  );
};

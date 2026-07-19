import { TextField, type TextFieldProps } from '@mui/material';
import {
  Controller,
  type Control,
  type FieldValues,
  type Path,
  type RegisterOptions,
} from 'react-hook-form';

type RHFTextFieldProps<T extends FieldValues, N extends Path<T>> = Omit<
  TextFieldProps,
  'name' | 'value' | 'error' | 'onChange' | 'onBlur' | 'ref'
> & {
  name: N;
  control: Control<T>;
  rules?: Omit<RegisterOptions<T, N>, 'valueAsNumber' | 'valueAsDate' | 'setValueAs' | 'disabled'>;
};

export const RHFTextField = <T extends FieldValues, N extends Path<T>>({
  name,
  control,
  rules,
  helperText,
  ...textFieldProps
}: RHFTextFieldProps<T, N>) => (
  <Controller
    name={name}
    control={control}
    rules={rules}
    render={({ field, fieldState }) => (
      <TextField
        {...textFieldProps}
        {...field}
        error={!!fieldState.error}
        helperText={fieldState.error?.message ?? helperText}
      />
    )}
  />
);

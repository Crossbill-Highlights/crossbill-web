import {
  Alert,
  Box,
  Button,
  Container,
  Divider,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import { createFileRoute } from '@tanstack/react-router';
import { FormEvent, useState } from 'react';
import { useUpdateMeApiV1UsersMePost } from '../api/generated/users/users';
import { useAuth } from '../context/AuthContext';

export const Route = createFileRoute('/settings')({
  component: SettingsPage,
});

function SettingsPage() {
  const { user, refreshUser } = useAuth();

  // Name form state
  const [name, setName] = useState(user?.name || '');
  const [nameError, setNameError] = useState<string | null>(null);
  const [nameSuccess, setNameSuccess] = useState(false);

  // Password form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  const updateMutation = useUpdateMeApiV1UsersMePost();

  const handleNameSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setNameError(null);
    setNameSuccess(false);

    if (!name.trim()) {
      setNameError('Name cannot be empty');
      return;
    }

    try {
      await updateMutation.mutateAsync({ data: { name: name.trim() } });
      await refreshUser();
      setNameSuccess(true);
    } catch {
      setNameError('Failed to update name');
    }
  };

  const handlePasswordSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);

    if (!currentPassword) {
      setPasswordError('Current password is required');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }

    try {
      await updateMutation.mutateAsync({
        data: {
          current_password: currentPassword,
          new_password: newPassword,
        },
      });
      setPasswordSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch {
      setPasswordError('Failed to update password. Check your current password.');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 6 }}>
      <Typography
        variant="h1"
        sx={{
          mb: 1,
          color: 'text.primary',
        }}
      >
        Settings
      </Typography>
      <Typography
        variant="body2"
        sx={{
          mb: 4,
          color: 'text.secondary',
        }}
      >
        Manage your account preferences
      </Typography>

      {/* Profile Section */}
      <Paper
        elevation={2}
        sx={{
          p: 4,
          mb: 3,
        }}
      >
        <Typography
          variant="h3"
          sx={{
            mb: 3,
            color: 'text.primary',
          }}
        >
          Profile
        </Typography>

        {nameSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Name updated successfully
          </Alert>
        )}

        {nameError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {nameError}
          </Alert>
        )}

        <Box component="form" onSubmit={handleNameSubmit}>
          <TextField
            label="Display Name"
            fullWidth
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              setNameSuccess(false);
            }}
            margin="normal"
            inputProps={{ maxLength: 100 }}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={updateMutation.isPending || name === user?.name}
            sx={{ mt: 2 }}
          >
            {updateMutation.isPending ? 'Saving...' : 'Update Name'}
          </Button>
        </Box>
      </Paper>

      {/* Password Section */}
      <Paper
        elevation={2}
        sx={{
          p: 4,
        }}
      >
        <Typography
          variant="h3"
          sx={{
            mb: 1,
            color: 'text.primary',
          }}
        >
          Change Password
        </Typography>
        <Typography
          variant="body2"
          sx={{
            mb: 3,
            color: 'text.secondary',
          }}
        >
          Update your password to keep your account secure
        </Typography>

        <Divider sx={{ mb: 3 }} />

        {passwordSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Password updated successfully
          </Alert>
        )}

        {passwordError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {passwordError}
          </Alert>
        )}

        <Box component="form" onSubmit={handlePasswordSubmit}>
          <TextField
            label="Current Password"
            type="password"
            fullWidth
            value={currentPassword}
            onChange={(e) => {
              setCurrentPassword(e.target.value);
              setPasswordSuccess(false);
            }}
            margin="normal"
            autoComplete="current-password"
          />
          <TextField
            label="New Password"
            type="password"
            fullWidth
            value={newPassword}
            onChange={(e) => {
              setNewPassword(e.target.value);
              setPasswordSuccess(false);
            }}
            margin="normal"
            autoComplete="new-password"
            helperText="Minimum 8 characters"
          />
          <TextField
            label="Confirm New Password"
            type="password"
            fullWidth
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              setPasswordSuccess(false);
            }}
            margin="normal"
            autoComplete="new-password"
          />
          <Button
            type="submit"
            variant="contained"
            disabled={updateMutation.isPending || !currentPassword || !newPassword || !confirmPassword}
            sx={{ mt: 2 }}
          >
            {updateMutation.isPending ? 'Updating...' : 'Update Password'}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}

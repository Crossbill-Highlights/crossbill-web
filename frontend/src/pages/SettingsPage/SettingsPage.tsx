import { useUpdateMeApiV1UsersMePost } from '@/api/generated/users/users';
import { PageContainer } from '@/components/layout/Layouts.tsx';
import { useAuth } from '@/context/AuthContext';
import { Alert, Box, Button, Divider, TextField, Typography } from '@mui/material';
import { FormEvent, useState } from 'react';

export const SettingsPage = () => {
  const { user, refreshUser } = useAuth();

  // Email form state
  const [email, setEmail] = useState(user?.email || '');
  const [emailError, setEmailError] = useState<string | null>(null);
  const [emailSuccess, setEmailSuccess] = useState(false);

  // Password form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  const updateMutation = useUpdateMeApiV1UsersMePost();

  const handleEmailSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setEmailError(null);
    setEmailSuccess(false);

    if (!email.trim()) {
      setEmailError('Email cannot be empty');
      return;
    }

    try {
      await updateMutation.mutateAsync({ data: { email: email.trim() } });
      await refreshUser();
      setEmailSuccess(true);
    } catch {
      setEmailError('Failed to update email');
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
    <PageContainer maxWidth="sm">
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
      <Box
        sx={{
          mb: 6,
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

        <Divider sx={{ mb: 3 }} />

        {emailSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Email updated successfully
          </Alert>
        )}

        {emailError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {emailError}
          </Alert>
        )}

        <Box component="form" onSubmit={handleEmailSubmit}>
          <TextField
            label="Email"
            fullWidth
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setEmailSuccess(false);
            }}
            margin="normal"
            inputProps={{ maxLength: 100 }}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={updateMutation.isPending || email === user?.email}
            sx={{ mt: 2 }}
          >
            {updateMutation.isPending ? 'Saving...' : 'Update Email'}
          </Button>
        </Box>
      </Box>

      {/* Password Section */}
      <Box>
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
            disabled={
              updateMutation.isPending || !currentPassword || !newPassword || !confirmPassword
            }
            sx={{ mt: 2 }}
          >
            {updateMutation.isPending ? 'Updating...' : 'Update Password'}
          </Button>
        </Box>
      </Box>
    </PageContainer>
  );
};

import { LogoutIcon, MenuIcon, SettingsIcon } from '@/components/common/Icons';
import {
  Box,
  Button,
  Container,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  AppBar as MuiAppBar,
  Toolbar,
  Typography,
} from '@mui/material';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

export function AppBar() {
  const { logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleMenuClose();
    logout();
  };

  return (
    <MuiAppBar
      position="sticky"
      elevation={2}
      sx={{
        backgroundColor: 'primary.main',
      }}
    >
      <Container maxWidth="xl" disableGutters>
        <Toolbar sx={{ gap: 2 }}>
          {/* Crossbill Icon and Title - Clickable */}
          <Box
            component={Link}
            to="/"
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              textDecoration: 'none',
              color: 'inherit',
              '&:hover': {
                opacity: 0.9,
              },
            }}
          >
            <Box
              component="img"
              src="/icon-transparent.png"
              alt="Crossbill"
              sx={{
                height: 40,
                width: 40,
              }}
            />

            <Typography
              variant="h6"
              component="div"
              sx={{
                fontWeight: 700,
                color: 'primary.contrastText',
              }}
            >
              Crossbill
            </Typography>
          </Box>

          {/* Navigation Items */}
          <Button
            component={Link}
            to="/"
            color="inherit"
            sx={{
              fontWeight: 500,
              color: 'primary.contrastText',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
              },
            }}
          >
            Home
          </Button>

          {/* Spacer */}
          <Box sx={{ flexGrow: 1 }} />

          {/* Hamburger menu */}
          <IconButton
            color="inherit"
            aria-label="Menu"
            onClick={handleMenuOpen}
            sx={{
              color: 'primary.contrastText',
            }}
          >
            <MenuIcon />
          </IconButton>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
          >
            <MenuItem component={Link} to="/settings" onClick={handleMenuClose}>
              <ListItemIcon>
                <SettingsIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Preferences</ListItemText>
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <LogoutIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Logout</ListItemText>
            </MenuItem>
          </Menu>
        </Toolbar>
      </Container>
    </MuiAppBar>
  );
}

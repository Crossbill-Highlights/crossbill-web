// design-sync bundle entry (generated for /design-sync — safe to delete when not syncing).
// Re-exports the scoped design-system primitives plus a DSProvider that wraps
// previews in the app's MUI theme. No JSX here so this file needs no tsconfig
// discovery; the imported .tsx sources resolve their own jsx via frontend/tsconfig.json.
import { theme } from '@/theme/theme';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider } from '@mui/material/styles';
import { createElement, type ReactNode } from 'react';

export const DSProvider = ({ children }: { children?: ReactNode }) =>
  createElement(ThemeProvider, { theme }, createElement(CssBaseline), children as ReactNode);

// Semantic icon set (re-exported from the app) so authored previews can pass
// icons that share the bundle's MUI instance and theme.
export * from '@/theme/Icons';

export { AIActionButton } from '@/components/buttons/AIActionButton';
export { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip';
export { ScrollToTopButton } from '@/components/buttons/ScrollToTopButton';
export { UnlinkButton } from '@/components/buttons/UnlinkButton';

export { RHFTextField } from '@/components/inputs/RHFTextField';
export { SearchBar } from '@/components/inputs/SearchBar';
export { TagInput } from '@/components/inputs/TagInput';

export { HighlightCard } from '@/components/cards/HighlightCard';
export { HoverableCardActionArea } from '@/components/cards/HoverableCardActionArea';
export { MetadataRow } from '@/components/cards/MetadataRow';

export { SectionTitle } from '@/components/typography/SectionTitle';

export { CommonDialog } from '@/components/dialogs/CommonDialog';
export { CommonDialogHorizontalNavigation } from '@/components/dialogs/CommonDialogHorizontalNavigation';
export { CommonDialogTitle } from '@/components/dialogs/CommonDialogTitle';
export { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog';
export { DialogTabs } from '@/components/dialogs/DialogTabs';
export { DialogToolbar } from '@/components/dialogs/DialogToolbar';
export { ProgressBar } from '@/components/dialogs/ProgressBar';

export { AppBar } from '@/components/layout/AppBar';
export { ContentWithSidebar, PageContainer } from '@/components/layout/Layouts';

export { Collapsable } from '@/components/animations/Collapsable';
export { FadeInOut } from '@/components/animations/FadeInOut';
export { Spinner } from '@/components/animations/Spinner';

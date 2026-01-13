import type { AppSettingsResponse } from '@/api/generated/model';
import { useSettings } from '@/context/SettingsContext';
import type { ReactNode } from 'react';

interface FeatureGateProps<K extends keyof AppSettingsResponse> {
  flag: K;
  value: AppSettingsResponse[K];
  children: ReactNode;
}

export function FeatureGate<K extends keyof AppSettingsResponse>({
  flag,
  value,
  children,
}: FeatureGateProps<K>) {
  const { settings, isLoading } = useSettings();

  // Don't render anything while loading
  if (isLoading) {
    return null;
  }

  // Don't render if settings are not available
  if (!settings) {
    return null;
  }

  // Only render children if the flag matches the expected value
  if (settings[flag] === value) {
    return <>{children}</>;
  }

  return null;
}

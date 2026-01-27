import type { FeatureFlags } from '@/api/generated/model';
import { useSettings } from '@/context/SettingsContext.tsx';
import type { ReactNode } from 'react';

interface FeatureGateProps<K extends keyof FeatureFlags> {
  flag: K;
  value: FeatureFlags[K];
  children: ReactNode;
}

export function FeatureGate<K extends keyof FeatureFlags>({
  flag,
  value,
  children,
}: FeatureGateProps<K>) {
  const { featureFlags, isLoading } = useSettings();

  // Don't render anything while loading
  if (isLoading) {
    return null;
  }

  // Don't render if settings are not available
  if (!featureFlags) {
    return null;
  }

  // Only render children if the flag matches the expected value
  if (featureFlags[flag] === value) {
    return <>{children}</>;
  }

  return null;
}

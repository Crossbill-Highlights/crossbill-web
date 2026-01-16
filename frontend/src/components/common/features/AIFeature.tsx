import type { ReactNode } from 'react';
import { FeatureGate } from './FeatureGate.tsx';

interface AIFeatureProps {
  children: ReactNode;
}

export function AIFeature({ children }: AIFeatureProps) {
  return (
    <FeatureGate flag="ai_features" value={true}>
      {children}
    </FeatureGate>
  );
}

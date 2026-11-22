import { useLocalSearchParams } from 'expo-router';
import type { ComponentType } from 'react';

import { ScreenMessage } from '@/components/screen-message';

/** Reads the [id] route param and renders the screen, or "not found" if it is not a number. */
export function withRecommendationId(Screen: ComponentType<{ id: number }>) {
  return function RecommendationRoute() {
    const { id } = useLocalSearchParams<{ id: string }>();
    const recommendationId = Number(id);
    if (!Number.isInteger(recommendationId)) {
      return <ScreenMessage title="Recommendation not found" />;
    }
    return <Screen id={recommendationId} />;
  };
}

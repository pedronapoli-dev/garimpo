import { useLocalSearchParams } from 'expo-router';
import type { ComponentType } from 'react';

import { ScreenMessage } from '@/components/screen-message';

/** Reads the [id] route param and renders the screen, or "not found" if it is not a number. */
export function withRouteId(Screen: ComponentType<{ id: number }>, notFound: string) {
  return function RouteWithId() {
    const { id } = useLocalSearchParams<{ id: string }>();
    const numericId = Number(id);
    if (!Number.isInteger(numericId)) {
      return <ScreenMessage title={notFound} />;
    }
    return <Screen id={numericId} />;
  };
}

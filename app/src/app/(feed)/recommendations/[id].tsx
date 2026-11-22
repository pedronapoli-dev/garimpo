import { useLocalSearchParams } from 'expo-router';

import { ScreenMessage } from '@/components/screen-message';
import { DetailScreen } from '@/features/recommendations/components/detail-screen';

export default function RecommendationRoute() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const recommendationId = Number(id);
  if (!Number.isInteger(recommendationId)) {
    return <ScreenMessage title="Recommendation not found" />;
  }
  return <DetailScreen id={recommendationId} />;
}

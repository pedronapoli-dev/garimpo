import { Stack } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';

import { formatDate } from '../format';
import { useFeed, useProfile } from '../queries';
import { RecommendationList } from './recommendation-list';

/** A curator's profile (FR7): who they are and what they recommended. */
export function ProfileScreen({ id }: { id: number }) {
  const profile = useProfile(id);
  const recommendations = useFeed({ sort: 'newest', genre: null, authorId: id });

  const header = profile.data ? (
    <View style={styles.header}>
      <ThemedText type="title" style={styles.name}>
        {profile.data.display_name}
      </ThemedText>
      <ThemedText themeColor="textSecondary">
        {profile.data.recommendation_count}{' '}
        {profile.data.recommendation_count === 1 ? 'recommendation' : 'recommendations'} · curator
        since {formatDate(profile.data.created_at)}
      </ThemedText>
    </View>
  ) : undefined;

  return (
    <ThemedView style={styles.container}>
      <Stack.Screen options={{ title: profile.data?.display_name ?? '' }} />
      <RecommendationList
        query={recommendations}
        header={header}
        errorTitle="Could not load this curator"
        emptyTitle="No recommendations yet"
      />
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { gap: Spacing.one, marginBottom: Spacing.two },
  name: { fontSize: 32, lineHeight: 38 },
});

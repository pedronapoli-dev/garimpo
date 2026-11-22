import { Stack } from 'expo-router';
import { ActivityIndicator, ScrollView, StyleSheet, View } from 'react-native';

import { errorMessage } from '@/api/errors';
import { Chip } from '@/components/chip';
import { ScreenMessage } from '@/components/screen-message';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';

import { TYPE_LABELS, formatDate, headline } from '../format';
import { useRecommendation } from '../queries';

export function DetailScreen({ id }: { id: number }) {
  const query = useRecommendation(id);

  if (query.isPending) {
    return <ActivityIndicator style={styles.loading} />;
  }
  if (query.isError) {
    return (
      <ScreenMessage
        title="Could not load this recommendation"
        message={errorMessage(query.error)}
        onRetry={() => query.refetch()}
      />
    );
  }

  const recommendation = query.data;
  return (
    <ThemedView style={styles.container}>
      <Stack.Screen options={{ title: TYPE_LABELS[recommendation.type] }} />
      <ScrollView contentContainerStyle={styles.content} contentInsetAdjustmentBehavior="automatic">
        <ThemedText type="title" style={styles.headline}>
          {headline(recommendation)}
        </ThemedText>
        <View style={styles.genres}>
          {recommendation.genres.map((genre) => (
            <Chip key={genre} label={genre} />
          ))}
        </View>
        <ThemedText type="smallBold" themeColor="textSecondary">
          Why listen
        </ThemedText>
        <ThemedText style={styles.text}>{recommendation.text}</ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          Recommended by {recommendation.author.display_name} on{' '}
          {formatDate(recommendation.created_at)}
        </ThemedText>
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  loading: { marginTop: Spacing.five },
  content: { padding: Spacing.four, gap: Spacing.three },
  headline: { fontSize: 32, lineHeight: 38 },
  genres: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.two },
  text: { fontSize: 17, lineHeight: 26 },
});

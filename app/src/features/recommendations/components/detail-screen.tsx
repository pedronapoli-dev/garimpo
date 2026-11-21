import { Stack, useRouter } from 'expo-router';
import { ActivityIndicator, Alert, ScrollView, StyleSheet, View } from 'react-native';

import { errorMessage } from '@/api/errors';
import { Button } from '@/components/button';
import { Chip } from '@/components/chip';
import { ScreenMessage } from '@/components/screen-message';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';
import { useSession } from '@/stores/session';

import { TYPE_LABELS, formatDate, headline } from '../format';
import { useDeleteRecommendation, useRecommendation } from '../queries';
import { SaveButton } from './save-button';
import { VoteButton } from './vote-button';

export function DetailScreen({ id }: { id: number }) {
  const query = useRecommendation(id);
  const userId = useSession((state) => state.user?.id);

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
        <View style={styles.row}>
          <VoteButton recommendation={recommendation} />
        </View>
        <ThemedText type="smallBold" themeColor="textSecondary">
          Why listen
        </ThemedText>
        <ThemedText style={styles.text}>{recommendation.text}</ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          Recommended by {recommendation.author.display_name} on{' '}
          {formatDate(recommendation.created_at)}
        </ThemedText>
        <SaveButton recommendation={recommendation} />
        {recommendation.author.id === userId ? <AuthorActions id={recommendation.id} /> : null}
      </ScrollView>
    </ThemedView>
  );
}

/** Rule 5: only the author sees these; the API enforces it again. */
function AuthorActions({ id }: { id: number }) {
  const router = useRouter();
  const remove = useDeleteRecommendation(id);

  function confirmDelete() {
    Alert.alert('Delete this recommendation?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: () => remove.mutate(undefined, { onSuccess: () => router.back() }),
      },
    ]);
  }

  return (
    <View style={styles.actions}>
      <Button
        title="Edit"
        variant="secondary"
        onPress={() => router.push(`/recommendations/${id}/edit`)}
      />
      <Button
        title="Delete"
        variant="secondary"
        onPress={confirmDelete}
        loading={remove.isPending}
      />
      {remove.isError ? <ThemedText>{errorMessage(remove.error)}</ThemedText> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  actions: { gap: Spacing.two, marginTop: Spacing.three },
  row: { flexDirection: 'row' },
  container: { flex: 1 },
  loading: { marginTop: Spacing.five },
  content: { padding: Spacing.four, gap: Spacing.three },
  headline: { fontSize: 32, lineHeight: 38 },
  genres: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.two },
  text: { fontSize: 17, lineHeight: 26 },
});

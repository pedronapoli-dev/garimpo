import { useState } from 'react';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet } from 'react-native';

import { errorMessage } from '@/api/errors';
import { ScreenMessage } from '@/components/screen-message';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';

import { useFeed } from '../queries';
import { GenreFilter } from './genre-filter';
import { RecommendationCard } from './recommendation-card';

export function FeedScreen() {
  const [genre, setGenre] = useState<string | null>(null);
  const feed = useFeed(genre);

  let body;
  if (feed.isPending) {
    body = <ActivityIndicator style={styles.loading} />;
  } else if (feed.isError) {
    body = (
      <ScreenMessage
        title="Could not load the feed"
        message={errorMessage(feed.error)}
        onRetry={() => feed.refetch()}
      />
    );
  } else {
    body = (
      <FlatList
        data={feed.data}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => <RecommendationCard recommendation={item} />}
        contentContainerStyle={styles.list}
        contentInsetAdjustmentBehavior="automatic"
        onEndReached={() => {
          if (feed.hasNextPage && !feed.isFetchingNextPage) feed.fetchNextPage();
        }}
        onEndReachedThreshold={0.5}
        refreshControl={
          <RefreshControl
            refreshing={feed.isRefetching && !feed.isFetchingNextPage}
            onRefresh={() => {
              void feed.refetch();
            }}
          />
        }
        ListFooterComponent={feed.isFetchingNextPage ? <ActivityIndicator /> : undefined}
        ListEmptyComponent={
          <ScreenMessage
            title="Nothing here yet"
            message={genre ? `No recommendations tagged ${genre}.` : 'Be the first to recommend.'}
          />
        }
      />
    );
  }

  return (
    <ThemedView style={styles.container}>
      <GenreFilter selected={genre} onSelect={setGenre} />
      {body}
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  loading: { marginTop: Spacing.five },
  list: { gap: Spacing.three, padding: Spacing.three, flexGrow: 1 },
});

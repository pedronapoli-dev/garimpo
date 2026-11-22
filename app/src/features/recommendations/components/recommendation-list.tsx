import type { UseInfiniteQueryResult } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet } from 'react-native';

import { errorMessage } from '@/api/errors';
import { ListMessage } from '@/components/screen-message';
import { Spacing } from '@/constants/theme';

import type { Recommendation } from '../types';
import { RecommendationCard } from './recommendation-card';

type RecommendationListProps = {
  query: UseInfiniteQueryResult<Recommendation[]>;
  emptyTitle: string;
  emptyMessage?: string;
  errorTitle: string;
  header?: ReactElement;
};

/** An infinite list of cards: the feed, the saved list and a profile. */
export function RecommendationList({
  query,
  emptyTitle,
  emptyMessage,
  errorTitle,
  header,
}: RecommendationListProps) {
  // Loading and errors render inside the list, so the header stays on screen
  // and iOS keeps insetting the content below the navigation bar.
  const placeholder = query.isPending ? (
    <ActivityIndicator style={styles.loading} />
  ) : query.isError ? (
    <ListMessage
      title={errorTitle}
      message={errorMessage(query.error)}
      onRetry={() => query.refetch()}
    />
  ) : (
    <ListMessage title={emptyTitle} message={emptyMessage} />
  );

  return (
    <FlatList
      data={query.data ?? []}
      keyExtractor={(item) => String(item.id)}
      renderItem={({ item }) => <RecommendationCard recommendation={item} />}
      ListHeaderComponent={header}
      contentContainerStyle={styles.list}
      contentInsetAdjustmentBehavior="automatic"
      onEndReached={() => {
        if (query.hasNextPage && !query.isFetchingNextPage) void query.fetchNextPage();
      }}
      onEndReachedThreshold={0.5}
      refreshControl={
        <RefreshControl
          refreshing={query.isRefetching && !query.isFetchingNextPage}
          onRefresh={() => {
            void query.refetch();
          }}
        />
      }
      ListFooterComponent={query.isFetchingNextPage ? <ActivityIndicator /> : undefined}
      ListEmptyComponent={placeholder}
    />
  );
}

const styles = StyleSheet.create({
  loading: { marginTop: Spacing.five },
  list: { gap: Spacing.three, padding: Spacing.three, flexGrow: 1 },
});

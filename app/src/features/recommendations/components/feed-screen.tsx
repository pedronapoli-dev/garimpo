import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { Chip } from '@/components/chip';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';

import { useFeed } from '../queries';
import type { FeedSort } from '../types';
import { GenreFilter } from './genre-filter';
import { RecommendationList } from './recommendation-list';

const SORTS: { value: FeedSort; label: string }[] = [
  { value: 'newest', label: 'Newest' },
  { value: 'top', label: 'Most voted' },
];

export function FeedScreen() {
  const [genre, setGenre] = useState<string | null>(null);
  const [sort, setSort] = useState<FeedSort>('newest');
  const feed = useFeed({ sort, genre, authorId: null });

  return (
    <ThemedView style={styles.container}>
      <View style={styles.sorts}>
        {SORTS.map((option) => (
          <Chip
            key={option.value}
            label={option.label}
            selected={sort === option.value}
            onPress={() => setSort(option.value)}
          />
        ))}
      </View>
      <GenreFilter selected={genre} onSelect={setGenre} />
      <RecommendationList
        query={feed}
        errorTitle="Could not load the feed"
        emptyTitle="Nothing here yet"
        emptyMessage={genre ? `No recommendations tagged ${genre}.` : 'Be the first to recommend.'}
      />
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  sorts: {
    flexDirection: 'row',
    gap: Spacing.two,
    paddingHorizontal: Spacing.three,
    paddingTop: Spacing.two,
  },
});

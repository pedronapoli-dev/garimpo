import { ScrollView, StyleSheet } from 'react-native';

import { Chip } from '@/components/chip';
import { Spacing } from '@/constants/theme';

import { useTags } from '../queries';

type GenreFilterProps = { selected: string | null; onSelect: (genre: string | null) => void };

export function GenreFilter({ selected, onSelect }: GenreFilterProps) {
  const { data: tags = [] } = useTags();
  return (
    <ScrollView
      testID="genre-filter"
      horizontal
      style={styles.filter}
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.row}>
      <Chip label="All" selected={selected === null} onPress={() => onSelect(null)} />
      {tags.map((tag) => (
        <Chip
          key={tag.id}
          label={tag.name}
          selected={selected === tag.name}
          onPress={() => onSelect(selected === tag.name ? null : tag.name)}
        />
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  // Without flexGrow: 0, a horizontal ScrollView takes all the height it can.
  // The negative margin lets the chips scroll to the screen's edges.
  filter: { flexGrow: 0, marginHorizontal: -Spacing.three },
  row: { gap: Spacing.two, paddingHorizontal: Spacing.three, paddingTop: Spacing.two },
});

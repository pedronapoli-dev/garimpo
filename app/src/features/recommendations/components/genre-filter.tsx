import { ScrollView, StyleSheet } from 'react-native';

import { Chip } from '@/components/chip';
import { Spacing } from '@/constants/theme';

import { useTags } from '../queries';

type GenreFilterProps = { selected: string | null; onSelect: (genre: string | null) => void };

export function GenreFilter({ selected, onSelect }: GenreFilterProps) {
  const { data: tags = [] } = useTags();
  return (
    <ScrollView
      horizontal
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
  row: { gap: Spacing.two, paddingHorizontal: Spacing.three, paddingVertical: Spacing.two },
});

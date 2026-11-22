import { ScrollView, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';

// A short version of docs/community-guidelines.md. Keep the two in sync.
const SECTIONS: { title: string; body: string }[] = [
  {
    title: 'Recommend what is lesser-known',
    body: 'Surface music that charts and algorithms miss: a regional scene, an out-of-print record, a forgotten album. There is no number; use judgment, and say why it is overlooked.',
  },
  {
    title: 'Explain why to listen',
    body: 'The text is the recommendation. Say what it sounds like and what makes it special, in your own words. Give a starting point for artists.',
  },
  {
    title: 'Tag honestly',
    body: 'Use 1 to 5 genres that describe the music. Reuse existing tags when they fit.',
  },
  {
    title: 'Be respectful',
    body: 'No hate or harassment. If a recommendation already exists, vote for it instead of posting it again. Say so when you recommend your own music.',
  },
  {
    title: 'Reports',
    body: 'Report what breaks these guidelines, not music you dislike. After 3 reports from different people, a recommendation is hidden until a maintainer reviews it.',
  },
];

export function GuidelinesScreen() {
  return (
    <ThemedView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} contentInsetAdjustmentBehavior="automatic">
        {SECTIONS.map((section) => (
          <View key={section.title} style={styles.section}>
            <ThemedText type="smallBold">{section.title}</ThemedText>
            <ThemedText>{section.body}</ThemedText>
          </View>
        ))}
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: Spacing.three, gap: Spacing.four },
  section: { gap: Spacing.one },
});

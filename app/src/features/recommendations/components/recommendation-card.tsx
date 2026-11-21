import { Link, useRouter } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

import { TYPE_LABELS, headline } from '../format';
import type { Recommendation } from '../types';
import { VoteButton } from './vote-button';

export function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  const theme = useTheme();
  const router = useRouter();
  return (
    <Link href={`/recommendations/${recommendation.id}`} asChild>
      <Pressable
        accessibilityRole="link"
        style={({ pressed }) => [
          styles.card,
          { backgroundColor: theme.backgroundElement },
          pressed && styles.pressed,
        ]}>
        <ThemedText type="small" themeColor="textSecondary">
          {TYPE_LABELS[recommendation.type]} · {recommendation.genres.join(', ')}
        </ThemedText>
        <ThemedText type="subtitle" style={styles.headline}>
          {headline(recommendation)}
        </ThemedText>
        <ThemedText numberOfLines={3}>{recommendation.text}</ThemedText>
        <View style={styles.footer}>
          <Pressable
            accessibilityRole="link"
            hitSlop={8}
            onPress={() => router.push(`/users/${recommendation.author.id}`)}>
            <ThemedText type="small" themeColor="textSecondary">
              by {recommendation.author.display_name}
            </ThemedText>
          </Pressable>
          <VoteButton recommendation={recommendation} />
        </View>
      </Pressable>
    </Link>
  );
}

const styles = StyleSheet.create({
  card: { padding: Spacing.three, borderRadius: Spacing.three, gap: Spacing.two },
  headline: { fontSize: 20, lineHeight: 26 },
  footer: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  pressed: { opacity: 0.8 },
});

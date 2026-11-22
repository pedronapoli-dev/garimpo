import { useRouter } from 'expo-router';
import { Pressable, StyleSheet } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { useSession } from '@/stores/session';

import { useVote } from '../queries';
import type { Recommendation } from '../types';

/** Rule 4 in the UI: authors see the count but cannot vote. */
export function VoteButton({ recommendation }: { recommendation: Recommendation }) {
  const theme = useTheme();
  const router = useRouter();
  const userId = useSession((state) => state.user?.id);
  const vote = useVote(recommendation.id);
  const own = recommendation.author.id === userId;
  const voted = recommendation.voted_by_me;
  const count = recommendation.vote_count;

  function press() {
    if (userId === undefined) {
      router.push('/account/login');
      return;
    }
    vote.mutate(!voted);
  }

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${voted ? 'Remove vote' : 'Vote'}, ${count} ${count === 1 ? 'vote' : 'votes'}`}
      accessibilityState={{ selected: voted, disabled: own }}
      disabled={own}
      hitSlop={8}
      onPress={press}
      style={[
        styles.button,
        { backgroundColor: voted ? theme.tint : theme.backgroundSelected },
        own && styles.own,
      ]}>
      <ThemedText type="smallBold" style={{ color: voted ? theme.onTint : theme.text }}>
        ▲ {count}
      </ThemedText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    paddingHorizontal: Spacing.three,
    paddingVertical: Spacing.one,
    borderRadius: Spacing.four,
    minWidth: 56,
    alignItems: 'center',
  },
  own: { opacity: 0.6 },
});

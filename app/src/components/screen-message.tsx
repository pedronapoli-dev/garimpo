import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { Button } from '@/components/button';
import { ScreenScrollView } from '@/components/screen-scroll-view';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';

type MessageProps = { title: string; message?: string; onRetry?: () => void };

/** An empty or error message, for a list that already handles the insets. */
export function ListMessage({ title, message, onRetry }: MessageProps) {
  return (
    <View style={styles.message}>
      <ThemedText type="subtitle" style={styles.center}>
        {title}
      </ThemedText>
      {message ? (
        <ThemedText themeColor="textSecondary" style={styles.center}>
          {message}
        </ThemedText>
      ) : null}
      {onRetry ? <Button title="Try again" variant="secondary" onPress={onRetry} /> : null}
    </View>
  );
}

/** Full-screen empty or error state. */
export function ScreenMessage(props: MessageProps) {
  return (
    <ThemedView style={styles.screen}>
      <ScreenScrollView contentContainerStyle={styles.centered} alwaysBounceVertical={false}>
        <ListMessage {...props} />
      </ScreenScrollView>
    </ThemedView>
  );
}

/** Full-screen loading state. */
export function ScreenLoading() {
  return (
    <ThemedView style={styles.screen}>
      <ScreenScrollView contentContainerStyle={styles.centered} alwaysBounceVertical={false}>
        <ActivityIndicator />
      </ScreenScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  centered: { flexGrow: 1, justifyContent: 'center' },
  message: {
    alignItems: 'center',
    gap: Spacing.three,
    padding: Spacing.four,
  },
  center: { textAlign: 'center' },
});

import { useRouter } from 'expo-router';
import { StyleSheet } from 'react-native';

import { Button } from '@/components/button';
import { ScreenScrollView } from '@/components/screen-scroll-view';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';

/** Shown in place of a screen that needs a logged-in user. */
export function SignInPrompt({ message }: { message: string }) {
  const router = useRouter();
  return (
    <ThemedView style={styles.screen}>
      <ScreenScrollView contentContainerStyle={styles.content} alwaysBounceVertical={false}>
        <ThemedText style={styles.center}>{message}</ThemedText>
        <Button title="Log in" onPress={() => router.push('/account/login')} />
        <Button
          title="I have an invite"
          variant="secondary"
          onPress={() => router.push('/account/signup')}
        />
      </ScreenScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { flexGrow: 1, justifyContent: 'center', gap: Spacing.three, padding: Spacing.four },
  center: { textAlign: 'center' },
});

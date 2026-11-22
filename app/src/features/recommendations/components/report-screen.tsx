import { useRouter } from 'expo-router';
import { useState } from 'react';
import { StyleSheet } from 'react-native';

import { errorMessage } from '@/api/errors';
import { Button } from '@/components/button';
import { TextField } from '@/components/text-field';
import { ScreenScrollView } from '@/components/screen-scroll-view';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { SignInPrompt } from '@/features/auth/components/sign-in-prompt';
import { useSession } from '@/stores/session';

import { useReport } from '../queries';

export const REASON_MAX = 500;

export function ReportScreen({ id }: { id: number }) {
  const signedIn = useSession((state) => state.status === 'signedIn');
  if (!signedIn) return <SignInPrompt message="Log in to report a recommendation." />;
  return <ReportForm id={id} />;
}

function ReportForm({ id }: { id: number }) {
  const router = useRouter();
  const theme = useTheme();
  const report = useReport(id);
  const [reason, setReason] = useState('');
  const trimmed = reason.trim();

  if (report.isSuccess) {
    return (
      <ThemedView style={styles.container}>
        <ScreenScrollView contentContainerStyle={styles.content}>
          <ThemedText type="subtitle">Thanks for the report</ThemedText>
          <ThemedText themeColor="textSecondary">
            After 3 reports from different people, a recommendation is hidden until a maintainer
            reviews it.
          </ThemedText>
          <Button title="Done" onPress={() => router.back()} />
        </ScreenScrollView>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={styles.container}>
      <ScreenScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <ThemedText themeColor="textSecondary">
          Report what breaks the community guidelines, not music you dislike.
        </ThemedText>
        <TextField
          label="Reason"
          value={reason}
          onChangeText={(value) => {
            setReason(value);
            if (report.isError) report.reset();
          }}
          hint={`${trimmed.length} / ${REASON_MAX}`}
          maxLength={REASON_MAX}
          multiline
          style={styles.textArea}
          textAlignVertical="top"
        />
        {report.isError ? (
          <ThemedText style={{ color: theme.danger }}>{errorMessage(report.error)}</ThemedText>
        ) : null}
        <Button
          title="Send report"
          onPress={() => report.mutate({ reason: trimmed })}
          disabled={trimmed.length === 0}
          loading={report.isPending}
        />
      </ScreenScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: Spacing.three, gap: Spacing.three },
  textArea: { minHeight: 120 },
});

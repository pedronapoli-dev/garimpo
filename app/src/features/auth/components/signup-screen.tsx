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

import { PASSWORD_MIN, type SignupForm, validateSignup } from '../form';
import { useSignup } from '../queries';

export function SignupScreen() {
  const router = useRouter();
  const theme = useTheme();
  const signup = useSignup();
  const [form, setForm] = useState<SignupForm>({
    inviteCode: '',
    email: '',
    displayName: '',
    password: '',
  });
  const [submitted, setSubmitted] = useState(false);
  const errors = submitted ? validateSignup(form) : {};

  function update<K extends keyof SignupForm>(field: K, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function submit() {
    setSubmitted(true);
    if (Object.keys(validateSignup(form)).length > 0) return;
    signup.mutate(form, { onSuccess: () => router.dismissTo('/account') });
  }

  return (
    <ThemedView style={styles.container}>
      <ScreenScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <ThemedText themeColor="textSecondary">
          Garimpo is invite-only. Ask a curator for a code.
        </ThemedText>
        <TextField
          label="Invite code"
          value={form.inviteCode}
          onChangeText={(value) => update('inviteCode', value)}
          error={errors.inviteCode}
          autoCapitalize="none"
          autoCorrect={false}
        />
        <TextField
          label="Email"
          value={form.email}
          onChangeText={(value) => update('email', value)}
          error={errors.email}
          autoCapitalize="none"
          keyboardType="email-address"
          textContentType="emailAddress"
        />
        <TextField
          label="Display name"
          value={form.displayName}
          onChangeText={(value) => update('displayName', value)}
          error={errors.displayName}
          textContentType="nickname"
        />
        <TextField
          label="Password"
          value={form.password}
          onChangeText={(value) => update('password', value)}
          error={errors.password}
          hint={`At least ${PASSWORD_MIN} characters`}
          secureTextEntry
          textContentType="newPassword"
        />
        {signup.isError ? (
          <ThemedText style={{ color: theme.danger }}>{errorMessage(signup.error)}</ThemedText>
        ) : null}
        <Button title="Create account" onPress={submit} loading={signup.isPending} />
      </ScreenScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: Spacing.three, gap: Spacing.three },
});

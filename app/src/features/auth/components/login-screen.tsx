import { Link, useRouter } from 'expo-router';
import { useState } from 'react';
import { ScrollView, StyleSheet } from 'react-native';

import { errorMessage } from '@/api/errors';
import { Button } from '@/components/button';
import { TextField } from '@/components/text-field';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

import { type LoginForm, validateLogin } from '../form';
import { useLogin } from '../queries';

export function LoginScreen() {
  const router = useRouter();
  const theme = useTheme();
  const login = useLogin();
  const [form, setForm] = useState<LoginForm>({ email: '', password: '' });
  const [submitted, setSubmitted] = useState(false);
  const errors = submitted ? validateLogin(form) : {};

  function submit() {
    setSubmitted(true);
    if (Object.keys(validateLogin(form)).length > 0) return;
    login.mutate(form, { onSuccess: () => router.dismissTo('/account') });
  }

  return (
    <ThemedView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <TextField
          label="Email"
          value={form.email}
          onChangeText={(email) => setForm({ ...form, email })}
          error={errors.email}
          autoCapitalize="none"
          autoComplete="email"
          keyboardType="email-address"
          textContentType="emailAddress"
        />
        <TextField
          label="Password"
          value={form.password}
          onChangeText={(password) => setForm({ ...form, password })}
          error={errors.password}
          secureTextEntry
          textContentType="password"
        />
        {login.isError ? (
          <ThemedText style={{ color: theme.danger }}>{errorMessage(login.error)}</ThemedText>
        ) : null}
        <Button title="Log in" onPress={submit} loading={login.isPending} />
        <Link href="/account/signup" replace>
          <ThemedText type="link">Have an invite? Create an account</ThemedText>
        </Link>
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: Spacing.three, gap: Spacing.three },
});

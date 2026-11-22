import { useRouter } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';

import { ApiError, errorMessage } from '@/api/errors';
import { Button } from '@/components/button';
import { TextField } from '@/components/text-field';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

import { type RecommendationForm, textCounter, validateForm } from '../form';
import { TypePicker } from './type-picker';

type RecommendationEditorProps = {
  initialForm: RecommendationForm;
  submitTitle: string;
  pending: boolean;
  error: unknown;
  /** Called with a form that already passed validation. */
  onSubmit: (form: RecommendationForm) => void;
  /** Called on every edit, so the screen can clear a previous API error. */
  onChange: () => void;
};

/** The form shared by the create and edit screens. */
export function RecommendationEditor({
  initialForm,
  submitTitle,
  pending,
  error,
  onSubmit,
  onChange,
}: RecommendationEditorProps) {
  const router = useRouter();
  const theme = useTheme();
  const [form, setForm] = useState(initialForm);
  const [submitted, setSubmitted] = useState(false);

  // Field errors appear only after the first submit, not while typing.
  const errors = submitted ? validateForm(form) : {};
  const counter = textCounter(form.text);
  const duplicateId =
    error instanceof ApiError && error.code === 'duplicate_recommendation'
      ? error.body.existing_id
      : undefined;

  function update<K extends keyof RecommendationForm>(field: K, value: RecommendationForm[K]) {
    setForm((current) => ({ ...current, [field]: value }));
    onChange();
  }

  function submit() {
    setSubmitted(true);
    if (Object.keys(validateForm(form)).length > 0) return;
    onSubmit(form);
  }

  return (
    <ThemedView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={styles.content}
          contentInsetAdjustmentBehavior="automatic"
          keyboardShouldPersistTaps="handled">
          <TypePicker value={form.type} onChange={(type) => update('type', type)} />
          <TextField
            label="Artist"
            value={form.artist}
            onChangeText={(value) => update('artist', value)}
            error={errors.artist}
            autoCapitalize="words"
          />
          {form.type !== 'artist' ? (
            <TextField
              label={form.type === 'album' ? 'Album title' : 'Track title'}
              value={form.title}
              onChangeText={(value) => update('title', value)}
              error={errors.title}
            />
          ) : null}
          <TextField
            label="Genres"
            value={form.genres}
            onChangeText={(value) => update('genres', value)}
            error={errors.genres}
            hint="1 to 5, separated by commas"
            autoCapitalize="none"
            placeholder="mpb, jazz"
          />
          <TextField
            label="Why listen"
            value={form.text}
            onChangeText={(value) => update('text', value)}
            error={errors.text}
            hint={counter.label}
            multiline
            style={styles.textArea}
            textAlignVertical="top"
          />

          {error ? (
            <View style={[styles.banner, { borderColor: theme.danger }]}>
              <ThemedText>{errorMessage(error)}</ThemedText>
              {duplicateId != null ? (
                <Button
                  title="Open the existing recommendation"
                  variant="secondary"
                  onPress={() => router.push(`/recommendations/${duplicateId}`)}
                />
              ) : null}
            </View>
          ) : null}

          <Button title={submitTitle} onPress={submit} loading={pending} />
        </ScrollView>
      </KeyboardAvoidingView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: Spacing.three, gap: Spacing.three },
  textArea: { minHeight: 160 },
  banner: { borderWidth: 1, borderRadius: Spacing.two, padding: Spacing.three, gap: Spacing.two },
});

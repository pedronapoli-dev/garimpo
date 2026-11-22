import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { Button } from '@/components/button';
import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

import { GENRES_MAX, type RecommendationForm, parseGenres } from '../../recommendations/form';
import { useAssistReview, useAssistStatus } from '../queries';
import type { AssistIn } from '../types';

type AssistPanelProps = {
  form: RecommendationForm;
  /** Adds genres to the form; the editor owns the form state. */
  onAddGenres: (genres: string[]) => void;
};

/** The curator assist (FR12): reviews the text and suggests existing genres. */
export function AssistPanel({ form, onAddGenres }: AssistPanelProps) {
  const status = useAssistStatus();
  const review = useAssistReview();
  const theme = useTheme();

  // Without an assist on the server, the editor looks exactly like the MVP.
  if (status.data?.enabled !== true) return null;

  const draft = toDraft(form);
  const ready = draft.artist.length > 0 && draft.text.length > 0;
  const current = parseGenres(form.genres);
  const suggestions = (review.result?.suggested_genres ?? []).filter(
    (genre) => !current.includes(genre),
  );

  return (
    <View style={[styles.panel, { borderColor: theme.border }]}>
      <Button
        title="Review my text"
        variant="secondary"
        onPress={() => review.start(draft)}
        loading={review.status === 'streaming' && review.feedback.length === 0}
        disabled={!ready || review.status === 'streaming'}
      />
      {review.status === 'streaming' && review.feedback.length > 0 ? (
        <ActivityIndicator accessibilityLabel="Reviewing" />
      ) : null}
      {review.feedback.length > 0 ? <ThemedText>{review.feedback}</ThemedText> : null}
      {review.result !== null ? (
        <ThemedText type="small">
          {review.result.explains_why
            ? 'Your text explains why to listen.'
            : 'Your text could say more about why to listen.'}
        </ThemedText>
      ) : null}
      {suggestions.length > 0 ? (
        <View style={styles.chips}>
          {suggestions.map((genre) => (
            <Button
              key={genre}
              title={`+ ${genre}`}
              variant="secondary"
              onPress={() => onAddGenres([genre])}
            />
          ))}
        </View>
      ) : null}
      {review.error !== null ? (
        <ThemedText style={{ color: theme.danger }}>{review.error}</ThemedText>
      ) : null}
    </View>
  );
}

function toDraft(form: RecommendationForm): AssistIn {
  const title = form.title.trim();
  return {
    type: form.type,
    artist: form.artist.trim(),
    title: form.type === 'artist' || title.length === 0 ? null : title,
    text: form.text.trim(),
    // The API accepts up to 5; the form reports any extra on submit.
    genres: parseGenres(form.genres).slice(0, GENRES_MAX),
  };
}

const styles = StyleSheet.create({
  panel: { borderWidth: 1, borderRadius: Spacing.two, padding: Spacing.three, gap: Spacing.two },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.two },
});

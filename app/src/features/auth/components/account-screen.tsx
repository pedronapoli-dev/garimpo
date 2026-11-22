import { useRouter } from 'expo-router';
import { Share, StyleSheet, View } from 'react-native';

import { errorMessage } from '@/api/errors';
import { Button } from '@/components/button';
import { ScreenScrollView } from '@/components/screen-scroll-view';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { useCreateInvite } from '@/features/invites/queries';
import { useSession } from '@/stores/session';

import { logOut } from '../queries';
import { SignInPrompt } from './sign-in-prompt';

export function AccountScreen() {
  const user = useSession((state) => state.user);
  if (user === null) {
    return <SignInPrompt message="Log in to recommend music and invite other curators." />;
  }
  return <SignedInAccount id={user.id} displayName={user.display_name} email={user.email} />;
}

type SignedInAccountProps = { id: number; displayName: string; email: string };

function SignedInAccount({ id, displayName, email }: SignedInAccountProps) {
  const theme = useTheme();
  const router = useRouter();
  const invite = useCreateInvite();

  return (
    <ThemedView style={styles.container}>
      <ScreenScrollView contentContainerStyle={styles.content}>
        <View>
          <ThemedText type="subtitle">{displayName}</ThemedText>
          <ThemedText themeColor="textSecondary">{email}</ThemedText>
        </View>

        <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
          <ThemedText type="smallBold">Invite a curator</ThemedText>
          <ThemedText themeColor="textSecondary">Each code works for one sign-up.</ThemedText>
          {invite.data ? (
            <>
              <ThemedText type="code" selectable accessibilityLabel="Invite code">
                {invite.data.code}
              </ThemedText>
              <Button
                title="Share code"
                variant="secondary"
                onPress={() =>
                  Share.share({
                    message: `Join me on Garimpo with the invite code ${invite.data.code}`,
                  })
                }
              />
            </>
          ) : null}
          {invite.isError ? (
            <ThemedText style={{ color: theme.danger }}>{errorMessage(invite.error)}</ThemedText>
          ) : null}
          <Button
            title={invite.data ? 'Generate another' : 'Generate invite'}
            onPress={() => invite.mutate()}
            loading={invite.isPending}
          />
        </View>

        <Button
          title="My recommendations"
          variant="secondary"
          onPress={() => router.navigate(`/users/${id}`)}
        />
        <Button title="Log out" variant="secondary" onPress={() => void logOut()} />
      </ScreenScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: Spacing.three, gap: Spacing.four },
  card: { padding: Spacing.three, borderRadius: Spacing.three, gap: Spacing.two },
});

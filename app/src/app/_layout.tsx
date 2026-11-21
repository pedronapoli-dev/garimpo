import { QueryClientProvider } from '@tanstack/react-query';
import { DarkTheme, DefaultTheme, ThemeProvider } from 'expo-router';
import { NativeTabs } from 'expo-router/native-tabs';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';
import { useColorScheme } from 'react-native';

import { queryClient } from '@/api/query-client';
import { useSession } from '@/stores/session';

// Keep the splash screen until the session is read from the Keychain, so the
// app never flashes the signed-out state for a signed-in user.
void SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const colorScheme = useColorScheme();
  const restoring = useSession((state) => state.status === 'restoring');

  useEffect(() => {
    void useSession.getState().restore();
  }, []);

  useEffect(() => {
    if (!restoring) void SplashScreen.hideAsync();
  }, [restoring]);

  if (restoring) return null;

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
        <NativeTabs>
          <NativeTabs.Trigger name="(feed)">
            <NativeTabs.Trigger.Label>Feed</NativeTabs.Trigger.Label>
            <NativeTabs.Trigger.Icon sf="music.note.list" md="queue_music" />
          </NativeTabs.Trigger>
          <NativeTabs.Trigger name="new">
            <NativeTabs.Trigger.Label>Recommend</NativeTabs.Trigger.Label>
            <NativeTabs.Trigger.Icon
              sf={{ default: 'plus.circle', selected: 'plus.circle.fill' }}
              md="add_circle"
            />
          </NativeTabs.Trigger>
          <NativeTabs.Trigger name="account">
            <NativeTabs.Trigger.Label>Account</NativeTabs.Trigger.Label>
            <NativeTabs.Trigger.Icon
              sf={{ default: 'person.crop.circle', selected: 'person.crop.circle.fill' }}
              md="account_circle"
            />
          </NativeTabs.Trigger>
        </NativeTabs>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

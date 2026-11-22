import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DarkTheme, DefaultTheme, ThemeProvider } from 'expo-router';
import { NativeTabs } from 'expo-router/native-tabs';
import { useState } from 'react';
import { useColorScheme } from 'react-native';

export default function RootLayout() {
  const colorScheme = useColorScheme();
  // Created once per app run, like a singleton held by the App struct.
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
        <NativeTabs>
          <NativeTabs.Trigger name="(feed)">
            <NativeTabs.Trigger.Label>Feed</NativeTabs.Trigger.Label>
            <NativeTabs.Trigger.Icon
              sf={{ default: 'music.note.list', selected: 'music.note.list' }}
              md="queue_music"
            />
          </NativeTabs.Trigger>
          <NativeTabs.Trigger name="new">
            <NativeTabs.Trigger.Label>Recommend</NativeTabs.Trigger.Label>
            <NativeTabs.Trigger.Icon
              sf={{ default: 'plus.circle', selected: 'plus.circle.fill' }}
              md="add_circle"
            />
          </NativeTabs.Trigger>
        </NativeTabs>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

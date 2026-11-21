import { Stack } from 'expo-router';

export const unstable_settings = { anchor: 'index' };

export default function FeedLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: 'Garimpo', headerLargeTitle: true }} />
      <Stack.Screen name="recommendations/[id]/index" options={{ title: '' }} />
      <Stack.Screen name="users/[id]" options={{ title: '' }} />
      <Stack.Screen
        name="recommendations/[id]/edit"
        options={{ title: 'Edit', presentation: 'modal' }}
      />
    </Stack>
  );
}

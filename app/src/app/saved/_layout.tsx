import { Stack } from 'expo-router';

export default function SavedLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: 'Listen later', headerLargeTitle: true }} />
    </Stack>
  );
}

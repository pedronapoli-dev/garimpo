import { Stack } from 'expo-router';

export default function NewLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: 'Recommend', headerLargeTitle: true }} />
      <Stack.Screen name="guidelines" options={{ title: 'Community guidelines' }} />
    </Stack>
  );
}

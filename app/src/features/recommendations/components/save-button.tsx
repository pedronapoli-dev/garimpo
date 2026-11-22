import { useRouter } from 'expo-router';

import { Button } from '@/components/button';
import { useSession } from '@/stores/session';

import { useSave } from '../queries';
import type { Recommendation } from '../types';

export function SaveButton({ recommendation }: { recommendation: Recommendation }) {
  const router = useRouter();
  const signedIn = useSession((state) => state.status === 'signedIn');
  const save = useSave(recommendation.id);
  const saved = recommendation.saved_by_me;

  return (
    <Button
      title={saved ? 'Saved to listen later' : 'Listen later'}
      variant={saved ? 'primary' : 'secondary'}
      onPress={() => (signedIn ? save.mutate(!saved) : router.push('/account/login'))}
    />
  );
}

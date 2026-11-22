import { SignInPrompt } from '@/features/auth/components/sign-in-prompt';
import { useSession } from '@/stores/session';

import { useSaved } from '../queries';
import { RecommendationList } from './recommendation-list';

export function SavedScreen() {
  const signedIn = useSession((state) => state.status === 'signedIn');
  if (!signedIn) return <SignInPrompt message="Log in to save recommendations to listen later." />;
  return <SavedList />;
}

function SavedList() {
  const saved = useSaved();
  return (
    <RecommendationList
      query={saved}
      errorTitle="Could not load your saved list"
      emptyTitle="Nothing saved yet"
      emptyMessage="Tap “Listen later” on a recommendation to keep it here."
    />
  );
}

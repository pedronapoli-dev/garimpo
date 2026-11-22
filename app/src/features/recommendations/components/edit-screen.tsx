import { useRouter } from 'expo-router';

import { errorMessage } from '@/api/errors';
import { ScreenLoading, ScreenMessage } from '@/components/screen-message';

import { formFromRecommendation, toCreatePayload } from '../form';
import { useRecommendation, useUpdateRecommendation } from '../queries';
import { RecommendationEditor } from './recommendation-editor';

export function EditScreen({ id }: { id: number }) {
  const router = useRouter();
  const query = useRecommendation(id);
  const update = useUpdateRecommendation(id);

  if (query.isPending) return <ScreenLoading />;
  if (query.isError) {
    return (
      <ScreenMessage
        title="Could not load this recommendation"
        message={errorMessage(query.error)}
      />
    );
  }

  return (
    <RecommendationEditor
      initialForm={formFromRecommendation(query.data)}
      submitTitle="Save changes"
      pending={update.isPending}
      error={update.error}
      onChange={() => update.isError && update.reset()}
      onSubmit={(form) => update.mutate(toCreatePayload(form), { onSuccess: () => router.back() })}
    />
  );
}

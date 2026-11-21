import { useRouter } from 'expo-router';
import { useState } from 'react';

import { SignInPrompt } from '@/features/auth/components/sign-in-prompt';
import { useSession } from '@/stores/session';

import { emptyForm, toCreatePayload } from '../form';
import { useCreateRecommendation } from '../queries';
import { RecommendationEditor } from './recommendation-editor';

export function CreateScreen() {
  const signedIn = useSession((state) => state.status === 'signedIn');
  if (!signedIn) return <SignInPrompt message="Log in to recommend music." />;
  return <CreateForm />;
}

function CreateForm() {
  const router = useRouter();
  const create = useCreateRecommendation();
  // Changing the key remounts the editor, which empties the form after publishing.
  const [formKey, setFormKey] = useState(0);

  return (
    <RecommendationEditor
      key={formKey}
      initialForm={emptyForm()}
      submitTitle="Publish"
      pending={create.isPending}
      error={create.error}
      onChange={() => create.isError && create.reset()}
      onSubmit={(form) =>
        create.mutate(toCreatePayload(form), {
          onSuccess: (created) => {
            setFormKey((key) => key + 1);
            router.push(`/recommendations/${created.id}`);
          },
        })
      }
    />
  );
}

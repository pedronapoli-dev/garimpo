import { useMutation } from '@tanstack/react-query';

import { client } from '@/api/client';
import { unwrap } from '@/api/errors';
import { queryClient } from '@/api/query-client';
import { useSession } from '@/stores/session';

import type { LoginForm, SignupForm } from './form';

export function useLogin() {
  const signIn = useSession((state) => state.signIn);
  return useMutation({
    mutationFn: async ({ email, password }: LoginForm) =>
      unwrap(await client.POST('/auth/login', { body: { email: email.trim(), password } })),
    onSuccess: signIn,
  });
}

export function useSignup() {
  const signIn = useSession((state) => state.signIn);
  return useMutation({
    mutationFn: async (form: SignupForm) =>
      unwrap(
        await client.POST('/auth/signup', {
          body: {
            invite_code: form.inviteCode.trim(),
            email: form.email.trim(),
            display_name: form.displayName.trim(),
            password: form.password,
          },
        }),
      ),
    onSuccess: signIn,
  });
}

/** Logout is local: the token is stateless, so forgetting it is enough. */
export async function logOut(): Promise<void> {
  await useSession.getState().signOut();
  // Cached data may depend on who was logged in (votes and saves, from slice 5).
  queryClient.clear();
}

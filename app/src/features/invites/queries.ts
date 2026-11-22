import { useMutation } from '@tanstack/react-query';

import { client } from '@/api/client';
import { unwrap } from '@/api/errors';

export function useCreateInvite() {
  return useMutation({
    mutationFn: async () => unwrap(await client.POST('/invites')),
  });
}

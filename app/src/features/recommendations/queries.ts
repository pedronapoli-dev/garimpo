import {
  type QueryClient,
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { client } from '@/api/client';
import { unwrap } from '@/api/errors';

import {
  type FeedData,
  type VoteState,
  applySave,
  applyVote,
  mergePages,
  rollbackVote,
  setVoteState,
  updateInPages,
} from './cache';
import type { FeedSort, Recommendation, RecommendationCreate, RecommendationUpdate } from './types';

export type FeedParams = { sort: FeedSort; genre: string | null; authorId: number | null };

/** One place for cache keys, so invalidation cannot drift from the queries. */
export const recommendationKeys = {
  all: ['recommendations'] as const,
  /** Every paginated list: the feed, a profile's list and the saved list. */
  lists: () => [...recommendationKeys.all, 'list'] as const,
  feed: (params: FeedParams) => [...recommendationKeys.lists(), 'feed', params] as const,
  saved: () => [...recommendationKeys.lists(), 'saved'] as const,
  detail: (id: number) => [...recommendationKeys.all, 'detail', id] as const,
};

export const tagKeys = { all: ['tags'] as const };
export const userKeys = { detail: (id: number) => ['users', id] as const };

export function useFeed({ sort, genre, authorId }: FeedParams) {
  return useInfiniteQuery({
    queryKey: recommendationKeys.feed({ sort, genre, authorId }),
    queryFn: async ({ pageParam }) =>
      unwrap(
        await client.GET('/recommendations', {
          params: { query: { sort, genre, author_id: authorId, cursor: pageParam } },
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor,
    select: (data) => mergePages(data.pages),
  });
}

export function useSaved() {
  return useInfiniteQuery({
    queryKey: recommendationKeys.saved(),
    queryFn: async ({ pageParam }) =>
      unwrap(await client.GET('/me/saves', { params: { query: { cursor: pageParam } } })),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor,
    select: (data) => mergePages(data.pages),
  });
}

export function useRecommendation(id: number) {
  return useQuery({
    queryKey: recommendationKeys.detail(id),
    queryFn: async () =>
      unwrap(
        await client.GET('/recommendations/{recommendation_id}', {
          params: { path: { recommendation_id: id } },
        }),
      ),
  });
}

export function useTags() {
  return useQuery({
    queryKey: tagKeys.all,
    queryFn: async () => unwrap(await client.GET('/tags')),
  });
}

export function useProfile(userId: number) {
  return useQuery({
    queryKey: userKeys.detail(userId),
    queryFn: async () =>
      unwrap(await client.GET('/users/{user_id}', { params: { path: { user_id: userId } } })),
  });
}

/** Applies `update` to a recommendation in its detail and in every cached list. */
export function updateCachedRecommendation(
  queryClient: QueryClient,
  id: number,
  update: (recommendation: Recommendation) => Recommendation,
): void {
  queryClient.setQueryData<Recommendation>(recommendationKeys.detail(id), (current) =>
    current === undefined ? undefined : update(current),
  );
  queryClient.setQueriesData<FeedData>({ queryKey: recommendationKeys.lists() }, (data) =>
    updateInPages(data, id, update),
  );
}

function findCached(queryClient: QueryClient, id: number): Recommendation | undefined {
  const detail = queryClient.getQueryData<Recommendation>(recommendationKeys.detail(id));
  if (detail !== undefined) return detail;
  for (const [, data] of queryClient.getQueriesData<FeedData>({
    queryKey: recommendationKeys.lists(),
  })) {
    for (const page of data?.pages ?? []) {
      const found = page.items.find((item) => item.id === id);
      if (found !== undefined) return found;
    }
  }
  return undefined;
}

/**
 * Optimistic vote: the count changes at once, rolls back if the request
 * fails, and settles on the server's state when it answers. PUT and DELETE
 * are idempotent, so a retried request cannot double count.
 */
export function useVote(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (voted: boolean) => {
      const options = { params: { path: { recommendation_id: id } } };
      return unwrap(
        voted
          ? await client.PUT('/recommendations/{recommendation_id}/vote', options)
          : await client.DELETE('/recommendations/{recommendation_id}/vote', options),
      );
    },
    onMutate: async (voted): Promise<{ previous: VoteState | undefined }> => {
      // Stop in-flight refetches from overwriting the optimistic value.
      await queryClient.cancelQueries({ queryKey: recommendationKeys.all });
      const cached = findCached(queryClient, id);
      const previous = cached && { vote_count: cached.vote_count, voted_by_me: cached.voted_by_me };
      updateCachedRecommendation(queryClient, id, (item) => applyVote(item, voted));
      return { previous };
    },
    onError: (_error, _voted, context) => {
      const previous = context?.previous;
      if (previous !== undefined) {
        updateCachedRecommendation(queryClient, id, (item) => rollbackVote(item, previous));
      }
    },
    onSuccess: (state) => {
      updateCachedRecommendation(queryClient, id, (item) => setVoteState(item, state));
    },
  });
}

/** Save for later. Optimistic like votes; the saved list refetches afterwards. */
export function useSave(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (saved: boolean) => {
      const options = { params: { path: { recommendation_id: id } } };
      return unwrap(
        saved
          ? await client.PUT('/recommendations/{recommendation_id}/save', options)
          : await client.DELETE('/recommendations/{recommendation_id}/save', options),
      );
    },
    onMutate: async (saved) => {
      await queryClient.cancelQueries({ queryKey: recommendationKeys.all });
      updateCachedRecommendation(queryClient, id, (item) => applySave(item, saved));
      return { saved };
    },
    onError: (_error, saved) => {
      updateCachedRecommendation(queryClient, id, (item) => applySave(item, !saved));
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: recommendationKeys.saved() }),
  });
}

function invalidateLists(queryClient: QueryClient) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: recommendationKeys.lists() }),
    queryClient.invalidateQueries({ queryKey: tagKeys.all }),
    queryClient.invalidateQueries({ queryKey: ['users'] }),
  ]);
}

export function useCreateRecommendation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: RecommendationCreate) =>
      unwrap(await client.POST('/recommendations', { body })),
    onSuccess: (created: Recommendation) => {
      // The detail screen opens next, so seed its cache instead of refetching.
      queryClient.setQueryData(recommendationKeys.detail(created.id), created);
      return invalidateLists(queryClient);
    },
  });
}

export function useUpdateRecommendation(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: RecommendationUpdate) =>
      unwrap(
        await client.PATCH('/recommendations/{recommendation_id}', {
          params: { path: { recommendation_id: id } },
          body,
        }),
      ),
    onSuccess: (updated: Recommendation) => {
      queryClient.setQueryData(recommendationKeys.detail(id), updated);
      return invalidateLists(queryClient);
    },
  });
}

export function useDeleteRecommendation(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () =>
      unwrap(
        await client.DELETE('/recommendations/{recommendation_id}', {
          params: { path: { recommendation_id: id } },
        }),
      ),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: recommendationKeys.detail(id) });
      return invalidateLists(queryClient);
    },
  });
}

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { client } from '@/api/client';
import { unwrap } from '@/api/errors';

import { mergePages } from './cache';
import type { Recommendation, RecommendationCreate, RecommendationUpdate } from './types';

/** One place for cache keys, so invalidation cannot drift from the queries. */
export const recommendationKeys = {
  all: ['recommendations'] as const,
  feeds: () => [...recommendationKeys.all, 'feed'] as const,
  feed: (genre: string | null) => [...recommendationKeys.feeds(), { genre }] as const,
  detail: (id: number) => [...recommendationKeys.all, 'detail', id] as const,
};

export const tagKeys = { all: ['tags'] as const };

export function useFeed(genre: string | null) {
  return useInfiniteQuery({
    queryKey: recommendationKeys.feed(genre),
    queryFn: async ({ pageParam }) =>
      unwrap(
        await client.GET('/recommendations', {
          params: { query: { genre, cursor: pageParam } },
        }),
      ),
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

export function useCreateRecommendation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: RecommendationCreate) =>
      unwrap(await client.POST('/recommendations', { body })),
    onSuccess: (created: Recommendation) => {
      // The detail screen opens next, so seed its cache instead of refetching.
      queryClient.setQueryData(recommendationKeys.detail(created.id), created);
      return Promise.all([
        queryClient.invalidateQueries({ queryKey: recommendationKeys.feeds() }),
        queryClient.invalidateQueries({ queryKey: tagKeys.all }),
      ]);
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
      return Promise.all([
        queryClient.invalidateQueries({ queryKey: recommendationKeys.feeds() }),
        queryClient.invalidateQueries({ queryKey: tagKeys.all }),
      ]);
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
      return queryClient.invalidateQueries({ queryKey: recommendationKeys.feeds() });
    },
  });
}

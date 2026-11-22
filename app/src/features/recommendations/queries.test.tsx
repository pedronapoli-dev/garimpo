import { act, renderHook, waitFor } from '@testing-library/react-native';

import { client } from '@/api/client';
import { ApiError } from '@/api/errors';
import { makePage, makeRecommendation } from '@/test-utils/fixtures';
import { createTestQueryClient, failure, ok, queryWrapper } from '@/test-utils/query';

import {
  recommendationKeys,
  useCreateRecommendation,
  useFeed,
  useRecommendation,
  useSave,
  useVote,
} from './queries';

jest.mock('@/api/client', () => ({
  client: { GET: jest.fn(), POST: jest.fn(), PUT: jest.fn(), DELETE: jest.fn() },
}));

const GET = client.GET as jest.Mock;
const POST = client.POST as jest.Mock;
const PUT = client.PUT as jest.Mock;
const FEED = { sort: 'newest', genre: null, authorId: null } as const;

afterEach(() => jest.resetAllMocks());

describe('useFeed', () => {
  it('loads the next page with the cursor and merges pages', async () => {
    GET.mockResolvedValueOnce(ok(makePage([3, 2], 'cursor-1'))).mockResolvedValueOnce(
      ok(makePage([1])),
    );
    const wrapper = queryWrapper(createTestQueryClient());

    const { result } = await renderHook(
      () => useFeed({ sort: 'newest', genre: 'jazz', authorId: null }),
      { wrapper },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    await act(() => result.current.fetchNextPage());

    await waitFor(() => expect(result.current.hasNextPage).toBe(false));
    expect(result.current.data?.map((item) => item.id)).toEqual([3, 2, 1]);
    expect(GET).toHaveBeenLastCalledWith('/recommendations', {
      params: { query: { sort: 'newest', genre: 'jazz', author_id: null, cursor: 'cursor-1' } },
    });
  });
});

describe('useRecommendation', () => {
  it('exposes the API error', async () => {
    GET.mockResolvedValue(failure(404, { code: 'recommendation_not_found', message: 'Gone.' }));
    const wrapper = queryWrapper(createTestQueryClient());

    const { result } = await renderHook(() => useRecommendation(9), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(ApiError);
    expect((result.current.error as ApiError).status).toBe(404);
  });
});

describe('useCreateRecommendation', () => {
  it('seeds the detail cache and invalidates the feeds', async () => {
    const created = makeRecommendation({ id: 7 });
    POST.mockResolvedValue(ok(created, 201));
    const queryClient = createTestQueryClient();
    queryClient.setQueryData(recommendationKeys.feed(FEED), { pages: [], pageParams: [] });
    const { result } = await renderHook(() => useCreateRecommendation(), {
      wrapper: queryWrapper(queryClient),
    });

    await act(() =>
      result.current.mutateAsync({
        type: 'album',
        artist: created.artist,
        title: created.title,
        genres: created.genres,
        text: created.text,
      }),
    );

    expect(queryClient.getQueryData(recommendationKeys.detail(7))).toEqual(created);
    expect(queryClient.getQueryState(recommendationKeys.feed(FEED))?.isInvalidated).toBe(true);
  });

  it('rejects with the duplicate error and its existing id', async () => {
    POST.mockResolvedValue(
      failure(409, { code: 'duplicate_recommendation', message: 'Taken.', existing_id: 3 }),
    );
    const { result } = await renderHook(() => useCreateRecommendation(), {
      wrapper: queryWrapper(createTestQueryClient()),
    });

    await act(async () => {
      await expect(
        result.current.mutateAsync({
          type: 'artist',
          artist: 'Azymuth',
          title: null,
          genres: ['jazz'],
          text: 'x'.repeat(80),
        }),
      ).rejects.toMatchObject({ status: 409, body: { existing_id: 3 } });
    });
  });
});

describe('useVote', () => {
  function seed(queryClient: ReturnType<typeof createTestQueryClient>) {
    const recommendation = makeRecommendation({ id: 5, vote_count: 2, voted_by_me: false });
    queryClient.setQueryData(recommendationKeys.detail(5), recommendation);
    queryClient.setQueryData(recommendationKeys.feed(FEED), {
      pages: [{ items: [recommendation], next_cursor: null }],
      pageParams: [null],
    });
  }

  function cachedCounts(queryClient: ReturnType<typeof createTestQueryClient>) {
    const detail = queryClient.getQueryData<{ vote_count: number }>(recommendationKeys.detail(5));
    const feed = queryClient.getQueryData<{ pages: { items: { vote_count: number }[] }[] }>(
      recommendationKeys.feed(FEED),
    );
    return [detail?.vote_count, feed?.pages[0].items[0].vote_count];
  }

  it('updates every cache at once, then takes the server count', async () => {
    let answer: (value: unknown) => void = () => undefined;
    PUT.mockReturnValue(new Promise((resolve) => (answer = resolve)));
    const queryClient = createTestQueryClient();
    seed(queryClient);
    const { result } = await renderHook(() => useVote(5), { wrapper: queryWrapper(queryClient) });

    await act(async () => {
      result.current.mutate(true);
    });
    expect(cachedCounts(queryClient)).toEqual([3, 3]);

    await act(async () => answer(ok({ vote_count: 9, voted_by_me: true })));
    await waitFor(() => expect(cachedCounts(queryClient)).toEqual([9, 9]));
  });

  it('rolls back when the request fails', async () => {
    PUT.mockResolvedValue(failure(500, 'boom'));
    const queryClient = createTestQueryClient();
    seed(queryClient);
    const { result } = await renderHook(() => useVote(5), { wrapper: queryWrapper(queryClient) });

    await act(async () => {
      await result.current.mutateAsync(true).catch(() => undefined);
    });

    expect(cachedCounts(queryClient)).toEqual([2, 2]);
    expect(
      queryClient.getQueryData<{ voted_by_me: boolean }>(recommendationKeys.detail(5))?.voted_by_me,
    ).toBe(false);
  });
});

describe('useSave', () => {
  it('rolls back when the request fails', async () => {
    PUT.mockResolvedValue(failure(500, 'boom'));
    const queryClient = createTestQueryClient();
    queryClient.setQueryData(
      recommendationKeys.detail(5),
      makeRecommendation({ id: 5, saved_by_me: false }),
    );
    const { result } = await renderHook(() => useSave(5), { wrapper: queryWrapper(queryClient) });

    await act(async () => {
      await result.current.mutateAsync(true).catch(() => undefined);
    });

    expect(
      queryClient.getQueryData<{ saved_by_me: boolean }>(recommendationKeys.detail(5))?.saved_by_me,
    ).toBe(false);
  });
});

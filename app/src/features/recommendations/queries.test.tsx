import { act, renderHook, waitFor } from '@testing-library/react-native';

import { client } from '@/api/client';
import { ApiError } from '@/api/errors';
import { makePage, makeRecommendation } from '@/test-utils/fixtures';
import { createTestQueryClient, failure, ok, queryWrapper } from '@/test-utils/query';

import { recommendationKeys, useCreateRecommendation, useFeed, useRecommendation } from './queries';

jest.mock('@/api/client', () => ({
  client: { GET: jest.fn(), POST: jest.fn() },
}));

const GET = client.GET as jest.Mock;
const POST = client.POST as jest.Mock;

afterEach(() => jest.resetAllMocks());

describe('useFeed', () => {
  it('loads the next page with the cursor and merges pages', async () => {
    GET.mockResolvedValueOnce(ok(makePage([3, 2], 'cursor-1'))).mockResolvedValueOnce(
      ok(makePage([1])),
    );
    const wrapper = queryWrapper(createTestQueryClient());

    const { result } = await renderHook(() => useFeed('jazz'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    await act(() => result.current.fetchNextPage());

    await waitFor(() => expect(result.current.hasNextPage).toBe(false));
    expect(result.current.data?.map((item) => item.id)).toEqual([3, 2, 1]);
    expect(GET).toHaveBeenLastCalledWith('/recommendations', {
      params: { query: { genre: 'jazz', cursor: 'cursor-1' } },
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
    queryClient.setQueryData(recommendationKeys.feed(null), { pages: [], pageParams: [] });
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
    expect(queryClient.getQueryState(recommendationKeys.feed(null))?.isInvalidated).toBe(true);
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

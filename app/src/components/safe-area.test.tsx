import { render, screen } from '@testing-library/react-native';
import type { ReactElement, ReactNode } from 'react';

import { client } from '@/api/client';
import { ScreenMessage } from '@/components/screen-message';
import { LoginScreen } from '@/features/auth/components/login-screen';
import { SignInPrompt } from '@/features/auth/components/sign-in-prompt';
import { SignupScreen } from '@/features/auth/components/signup-screen';
import { FeedScreen } from '@/features/recommendations/components/feed-screen';
import { ReportScreen } from '@/features/recommendations/components/report-screen';
import { makePage } from '@/test-utils/fixtures';
import { createTestQueryClient, failure, ok, queryWrapper } from '@/test-utils/query';
import { isInsideInsetScrollView } from '@/test-utils/safe-area';
import { signInAs, signOutForTest } from '@/test-utils/session';

jest.mock('expo-router', () => ({
  Link: ({ children }: { children: ReactNode }) => children,
  Stack: { Screen: () => null },
  useRouter: () => ({ push: jest.fn(), back: jest.fn(), dismissTo: jest.fn() }),
}));
jest.mock('@/api/client', () => ({ client: { GET: jest.fn(), POST: jest.fn() } }));

const GET = client.GET as jest.Mock;

afterEach(() => {
  jest.resetAllMocks();
  signOutForTest();
});

function renderScreen(ui: ReactElement) {
  return render(ui, { wrapper: queryWrapper(createTestQueryClient()) });
}

function mockFeed(feed: () => unknown) {
  GET.mockImplementation(async (path: string) =>
    path === '/tags' ? ok([{ id: 1, name: 'jazz' }]) : feed(),
  );
}

describe('the feed stays below the navigation bar', () => {
  it('with recommendations', async () => {
    mockFeed(() => ok(makePage([1])));
    await renderScreen(<FeedScreen />);

    await screen.findByText('Arthur Verocai — Album 1');
    expect(isInsideInsetScrollView(screen.getByRole('button', { name: 'Newest' }))).toBe(true);
    expect(isInsideInsetScrollView(screen.getByRole('button', { name: 'jazz' }))).toBe(true);
  });

  it('while loading', async () => {
    mockFeed(() => new Promise(() => undefined));
    await renderScreen(<FeedScreen />);

    expect(isInsideInsetScrollView(screen.getByRole('button', { name: 'Newest' }))).toBe(true);
  });

  it('after an error, keeping the filters and the retry', async () => {
    mockFeed(() => failure(500, { code: 'x', message: 'Broken.' }));
    await renderScreen(<FeedScreen />);

    const retry = await screen.findByRole('button', { name: 'Try again' });
    expect(isInsideInsetScrollView(retry)).toBe(true);
    expect(isInsideInsetScrollView(screen.getByRole('button', { name: 'Newest' }))).toBe(true);
  });
});

it('keeps the genre row at its own height', async () => {
  mockFeed(() => ok(makePage([1])));
  await renderScreen(<FeedScreen />);

  const row = await screen.findByTestId('genre-filter');
  expect(row).toHaveStyle({ flexGrow: 0 });
});

describe('every other screen is inset', () => {
  it('a full-screen message', async () => {
    await renderScreen(<ScreenMessage title="Not found" />);
    expect(isInsideInsetScrollView(screen.getByText('Not found'))).toBe(true);
  });

  it('the sign-in prompt', async () => {
    await renderScreen(<SignInPrompt message="Log in." />);
    expect(isInsideInsetScrollView(screen.getByText('Log in.'))).toBe(true);
  });

  it('login', async () => {
    await renderScreen(<LoginScreen />);
    expect(isInsideInsetScrollView(screen.getByText('Email'))).toBe(true);
  });

  it('signup', async () => {
    await renderScreen(<SignupScreen />);
    expect(isInsideInsetScrollView(screen.getByText('Email'))).toBe(true);
  });

  it('report', async () => {
    signInAs();
    await renderScreen(<ReportScreen id={1} />);
    expect(isInsideInsetScrollView(screen.getByRole('button', { name: /report/i }))).toBe(true);
  });
});

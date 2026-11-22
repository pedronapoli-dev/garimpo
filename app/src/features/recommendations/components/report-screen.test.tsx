import { fireEvent, render, screen } from '@testing-library/react-native';

import { client } from '@/api/client';
import { createTestQueryClient, failure, ok, queryWrapper } from '@/test-utils/query';
import { signInAs } from '@/test-utils/session';

import { ReportScreen } from './report-screen';

jest.mock('expo-router', () => ({ useRouter: () => ({ back: jest.fn(), push: jest.fn() }) }));
jest.mock('@/api/client', () => ({ client: { POST: jest.fn() } }));

const POST = client.POST as jest.Mock;

beforeEach(() => signInAs());
afterEach(() => jest.resetAllMocks());

async function sendReport(reason: string) {
  await render(<ReportScreen id={4} />, { wrapper: queryWrapper(createTestQueryClient()) });
  await fireEvent.changeText(screen.getByLabelText('Reason'), reason);
  await fireEvent.press(screen.getByRole('button', { name: 'Send report' }));
}

it('sends the trimmed reason and thanks the user', async () => {
  POST.mockResolvedValue(
    ok({ id: 1, reason: 'Too famous.', created_at: '2026-11-21T12:00:00Z' }, 201),
  );

  await sendReport('  Too famous.  ');

  expect(await screen.findByText('Thanks for the report')).toBeOnTheScreen();
  expect(POST).toHaveBeenCalledWith('/recommendations/{recommendation_id}/reports', {
    params: { path: { recommendation_id: 4 } },
    body: { reason: 'Too famous.' },
  });
});

it('shows that the user already reported it', async () => {
  POST.mockResolvedValue(
    failure(409, {
      code: 'already_reported',
      message: 'You already reported this recommendation.',
    }),
  );

  await sendReport('Too famous.');

  expect(await screen.findByText('You already reported this recommendation.')).toBeOnTheScreen();
});

it('cannot send an empty reason', async () => {
  await render(<ReportScreen id={4} />, { wrapper: queryWrapper(createTestQueryClient()) });

  expect(screen.getByRole('button', { name: 'Send report' })).toBeDisabled();
});

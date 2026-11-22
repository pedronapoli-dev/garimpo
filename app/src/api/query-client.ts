import { QueryClient } from '@tanstack/react-query';

/** The app's single cache. Tests build their own with createTestQueryClient. */
export const queryClient = new QueryClient();

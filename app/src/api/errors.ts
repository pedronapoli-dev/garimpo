import type { components } from './schema';

export type ErrorOut = components['schemas']['ErrorOut'];

/** An error response from the API, always shaped as ErrorOut. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly body: ErrorOut,
  ) {
    super(body.message);
    this.name = 'ApiError';
  }

  get code(): string {
    return this.body.code;
  }
}

const UNKNOWN_ERROR: ErrorOut = {
  code: 'unknown_error',
  message: 'Something went wrong. Try again.',
};

function isErrorOut(value: unknown): value is ErrorOut {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as ErrorOut).code === 'string' &&
    typeof (value as ErrorOut).message === 'string'
  );
}

type Result<T> = { data?: T; error?: unknown; response: Response };

/**
 * Turns an openapi-fetch result into its data, or throws an ApiError.
 * TanStack Query expects query functions to throw on failure.
 */
export function unwrap<T>({ data, error, response }: Result<T>): T {
  if (error !== undefined || !response.ok) {
    throw new ApiError(response.status, isErrorOut(error) ? error : UNKNOWN_ERROR);
  }
  return data as T;
}

/** A message to show the user for any error a query or mutation throws. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return 'Could not reach the server. Check your connection and try again.';
}

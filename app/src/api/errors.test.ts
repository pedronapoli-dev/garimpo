import { ApiError, errorMessage, unwrap } from './errors';

function response(status: number): Response {
  return { ok: status >= 200 && status < 300, status } as Response;
}

describe('unwrap', () => {
  it('returns the data of a successful response', () => {
    expect(unwrap({ data: { id: 1 }, response: response(200) })).toEqual({ id: 1 });
  });

  it('returns undefined for an empty 204 response', () => {
    expect(unwrap({ response: response(204) })).toBeUndefined();
  });

  it('throws an ApiError carrying the ErrorOut body', () => {
    const body = { code: 'duplicate_recommendation', message: 'Taken.', existing_id: 3 };

    expect(() => unwrap({ error: body, response: response(409) })).toThrow(ApiError);
    try {
      unwrap({ error: body, response: response(409) });
    } catch (error) {
      expect((error as ApiError).status).toBe(409);
      expect((error as ApiError).body).toEqual(body);
      expect((error as ApiError).code).toBe('duplicate_recommendation');
    }
  });

  it('falls back to a generic body when the error is not ErrorOut', () => {
    expect(() => unwrap({ error: 'Bad Gateway', response: response(502) })).toThrow(
      'Something went wrong. Try again.',
    );
  });
});

describe('errorMessage', () => {
  it('uses the API message for an ApiError', () => {
    expect(errorMessage(new ApiError(404, { code: 'x', message: 'Not here.' }))).toBe('Not here.');
  });

  it('explains network failures', () => {
    expect(errorMessage(new TypeError('Network request failed'))).toMatch(/connection/);
  });
});

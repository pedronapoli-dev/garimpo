import { type SignupForm, validateLogin, validateSignup } from './form';

function signup(overrides: Partial<SignupForm> = {}): SignupForm {
  return {
    inviteCode: 'HDTUxtYISmYL',
    email: 'pedro@example.com',
    displayName: 'Pedro',
    password: 'a long password',
    ...overrides,
  };
}

describe('validateLogin', () => {
  it('accepts an email and a password', () => {
    expect(validateLogin({ email: 'pedro@example.com', password: 'x' })).toEqual({});
  });

  it.each(['', 'pedro', 'pedro@'])('rejects the email %j', (email) => {
    expect(validateLogin({ email, password: 'x' }).email).toBeDefined();
  });

  it('requires a password', () => {
    expect(validateLogin({ email: 'pedro@example.com', password: '' }).password).toBeDefined();
  });
});

describe('validateSignup', () => {
  it('accepts a complete form', () => {
    expect(validateSignup(signup())).toEqual({});
  });

  it('requires the invite code', () => {
    expect(validateSignup(signup({ inviteCode: ' ' })).inviteCode).toBeDefined();
  });

  it('requires a display name', () => {
    expect(validateSignup(signup({ displayName: '  ' })).displayName).toBeDefined();
  });

  it('requires 8 characters of password', () => {
    expect(validateSignup(signup({ password: '1234567' })).password).toBeDefined();
    expect(validateSignup(signup({ password: '12345678' }))).toEqual({});
  });
});

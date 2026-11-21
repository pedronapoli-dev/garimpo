// The API validates these again; the app checks them only for quick feedback.
export const PASSWORD_MIN = 8;

export type LoginForm = { email: string; password: string };
export type SignupForm = LoginForm & { inviteCode: string; displayName: string };
export type Errors<T> = Partial<Record<keyof T, string>>;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateLogin(form: LoginForm): Errors<LoginForm> {
  const errors: Errors<LoginForm> = {};
  if (!EMAIL_PATTERN.test(form.email.trim())) errors.email = 'Enter a valid email.';
  if (form.password.length === 0) errors.password = 'Enter your password.';
  return errors;
}

export function validateSignup(form: SignupForm): Errors<SignupForm> {
  const errors: Errors<SignupForm> = {};
  if (form.inviteCode.trim().length === 0) errors.inviteCode = 'Enter your invite code.';
  if (!EMAIL_PATTERN.test(form.email.trim())) errors.email = 'Enter a valid email.';
  if (form.displayName.trim().length === 0) errors.displayName = 'Enter the name curators see.';
  if (form.password.length < PASSWORD_MIN) {
    errors.password = `Use at least ${PASSWORD_MIN} characters.`;
  }
  return errors;
}

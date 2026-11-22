import createClient from 'openapi-fetch';

import type { paths } from './schema';

// The iOS simulator reaches the Mac at localhost. On a device or the Android
// emulator, set EXPO_PUBLIC_API_URL in app/.env.local (for example
// http://10.0.2.2:8000 or http://<your-mac-ip>:8000).
export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

export const client = createClient<paths>({ baseUrl: API_URL });

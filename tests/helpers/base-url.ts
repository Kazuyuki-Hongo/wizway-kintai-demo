import * as dotenv from 'dotenv';

dotenv.config({ path: '.env' });

/** 画面のベース URL（末尾スラッシュなし）。 */
export function getBaseUrl(): string {
  return (process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5173').replace(
    /\/$/,
    '',
  );
}

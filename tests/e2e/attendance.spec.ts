import { test, expect, Locator } from '@playwright/test';
import { getBaseUrl } from '../helpers/base-url';

function summaryBlock(summary: Locator, label: string) {
  return summary.locator('div').filter({ hasText: label }).locator('dd');
}

/**
 * 勤怠デモ（読み取り専用）。ログインなし。
 * ローカルは playwright.config の webServer が API + Vite を起動する。
 * デプロイ済みを見るときは PLAYWRIGHT_BASE_URL を設定する。
 */
test.describe('勤怠デモ', () => {
  test('社員と月を選ぶと行と合計が出る', async ({ page }) => {
    const base = getBaseUrl();
    await page.goto(`${base}/`, { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByRole('heading', { name: '勤怠デモ（読み取り専用）' }),
    ).toBeVisible();
    await expect(page.getByText('保存操作はありません')).toBeVisible();
    await expect(page.getByRole('button', { name: /保存/ })).toHaveCount(0);

    await expect(page.getByLabel('社員')).toBeVisible();
    await page.getByLabel('月').fill('2026-11');

    const summary = page.locator('dl.summary');
    await expect(summaryBlock(summary, '出勤日数')).toHaveText('3');
    await expect(summaryBlock(summary, '総実働（時間）')).toHaveText('17');
    await expect(summaryBlock(summary, '8時間超過（時間）')).toHaveText('1');
    await expect(summaryBlock(summary, '退勤なし件数')).toHaveText('1');

    const table = page.getByRole('table');
    await expect(table.getByRole('cell', { name: '2026-11-04' })).toBeVisible();
    await expect(table.getByRole('cell', { name: '（空）' }).first()).toBeVisible();
    await expect(table.getByRole('cell', { name: '欠勤' })).toBeVisible();
  });

  test('別のダミー社員に切り替えられる', async ({ page }) => {
    const base = getBaseUrl();
    await page.goto(`${base}/`, { waitUntil: 'domcontentloaded' });

    await page.getByLabel('社員').selectOption({ label: 'サンプル海原' });
    await page.getByLabel('月').fill('2026-11');

    const summary = page.locator('dl.summary');
    await expect(summaryBlock(summary, '出勤日数')).toHaveText('2');
    await expect(page.getByRole('cell', { name: '2026-11-02' })).toBeVisible();
    await expect(page.getByRole('cell', { name: '欠勤' })).toHaveCount(0);
  });
});

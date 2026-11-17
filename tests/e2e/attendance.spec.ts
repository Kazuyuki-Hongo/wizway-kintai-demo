import { test, expect, Locator } from '@playwright/test';
import { getBaseUrl } from '../helpers/base-url';

function summaryBlock(summary: Locator, label: string) {
  return summary.locator('div').filter({ hasText: label }).locator('dd');
}

/**
 * 勤怠デモ。ログインなし。保存は実行環境のコピーだけ。
 * ローカルは playwright.config の webServer が API + Vite を起動する。
 * デプロイ済みを見るときは PLAYWRIGHT_BASE_URL を設定する。
 */
test.describe('勤怠デモ', () => {
  test('空日は表示され、保存済みの日を変えると合計が変わる', async ({ page }) => {
    const base = getBaseUrl();
    await page.goto(`${base}/`, { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: '勤怠デモ' })).toBeVisible();
    await expect(page.getByText('初期データに戻ります')).toBeVisible();

    await expect(page.getByLabel('社員')).toBeVisible();
    await page.getByLabel('月').fill('2026-11');

    await expect(page.getByRole('cell', { name: '2026-11-01' })).toBeVisible();
    await expect(
      page.getByRole('button', { name: '2026-11-01 を保存' }),
    ).toHaveCount(0);

    const summary = page.locator('dl.summary');
    await expect(summaryBlock(summary, '出勤日数')).toHaveText('3');
    await expect(summaryBlock(summary, '総実働（時間）')).toHaveText('17');
    await expect(summaryBlock(summary, '8時間超過（時間）')).toHaveText('1');
    await expect(summaryBlock(summary, '退勤なし件数')).toHaveText('1');

    await page.getByLabel('2026-11-02 退勤').fill('19:00');
    await page.getByRole('button', { name: '2026-11-02 を保存' }).click();

    await expect(summaryBlock(summary, '総実働（時間）')).toHaveText('18');
    await expect(summaryBlock(summary, '8時間超過（時間）')).toHaveText('2');
    await expect(page.getByLabel('2026-11-05 区分')).toHaveValue('欠勤');
  });

  test('退勤が出勤より前だと保存が拒否される', async ({ page }) => {
    const base = getBaseUrl();
    await page.goto(`${base}/`, { waitUntil: 'domcontentloaded' });
    await page.getByLabel('月').fill('2026-11');

    await page.getByLabel('2026-11-02 退勤').fill('08:00');
    await page.getByRole('button', { name: '2026-11-02 を保存' }).click();
    await expect(page.locator('p.error')).toContainText('clock_out before clock_in');
  });

  test('別のダミー社員に切り替えられる', async ({ page }) => {
    const base = getBaseUrl();
    await page.goto(`${base}/`, { waitUntil: 'domcontentloaded' });

    await page.getByLabel('社員').selectOption({ label: 'サンプル海原' });
    await page.getByLabel('月').fill('2026-11');

    const summary = page.locator('dl.summary');
    await expect(summaryBlock(summary, '出勤日数')).toHaveText('2');
    await expect(
      page.getByRole('cell', { name: '2026-11-02', exact: true }),
    ).toBeVisible();
    await expect(page.getByLabel('2026-11-05 区分')).toHaveCount(0);
  });
});

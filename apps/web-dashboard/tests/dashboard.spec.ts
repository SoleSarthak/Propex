import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('should display security overview title', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Security Overview')).toBeVisible();
  });

  test('should show stat cards', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Active CVEs')).toBeVisible();
    await expect(page.getByText('Affected Packages')).toBeVisible();
  });
});

// Isolated UI fixture only. The fixture server CSP forbids external transport.
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

const base = 'http://127.0.0.1:3190';
const output = resolve('../docs/screenshots');
await mkdir(output, { recursive: true });
const edge = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || (existsSync(edge) ? edge : undefined);
const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
try {
  for (const [name, width, height] of [['pc', 1280, 900], ['390', 390, 844]]) {
    const page = await browser.newPage({ viewport: { width, height } });
    for (const route of ['/dashboard', '/financials', '/error']) {
      await page.goto(`${base}/?page=${encodeURIComponent(route)}`);
      const heading = page.locator('h1').first();
      await heading.waitFor();
      if (route === '/error') {
        const button = page.getByRole('button', { name: '再読み込み' });
        const color = await heading.evaluate(node => getComputedStyle(node).color);
        if (color === 'rgb(255, 255, 255)' || !(await button.isVisible()) || !(await button.isEnabled())) {
          throw new Error(`Error state contrast/action failed at ${name}`);
        }
        await page.screenshot({ path: resolve(output, `release-20260918-error-${name}.png`), fullPage: true });
        await button.click();
        await page.getByText('今日の対応と収益').first().waitFor();
      } else {
        if (route === '/financials') {
          await page.getByText('今月の売上・入金・原価・粗利').waitFor();
        }
        await page.screenshot({ path: resolve(output, `release-20260918-${route.slice(1)}-${name}.png`), fullPage: true });
      }
      console.log(`${name} ${route}: PASS`);
    }
    await page.close();
  }
} finally {
  await browser.close();
}

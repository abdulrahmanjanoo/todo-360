// Screenshots of every screen for the design critic. Run against a live server:
//   TODO360_URL=http://127.0.0.1:8362 node qa/shots.js [outdir]
const { chromium } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

(async () => {
  const base = process.env.TODO360_URL || 'http://127.0.0.1:8360';
  const out = process.argv[2] || path.join(__dirname, 'shots');
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const shots = [
    ['focus', '/#/'], ['todos', '/#/todos?owner=me&money=0'], ['todos-money', '/#/todos?owner=me&money=1'],
    ['meetings', '/#/meetings'], ['gaps', '/#/gaps'],
  ];
  for (const scheme of ['dark', 'light']) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: scheme, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    for (const [name, h] of shots) {
      await page.goto(base + h);
      await page.waitForSelector('h1.lt');
      await page.waitForTimeout(300);
      await page.screenshot({ path: path.join(out, `${name}-${scheme}.png`), fullPage: name === 'focus' });
    }
    // first meeting sheet
    await page.goto(base + '/#/meetings');
    await page.waitForSelector('a.row.link');
    const href = await page.locator('a.row.link').first().getAttribute('href');
    await page.goto(base + '/' + href);
    await page.waitForSelector('.sheet');
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(out, `sheet-${scheme}.png`) });
    await ctx.close();
  }
  // a real phone: touch and no hover, so the per-row chip shows
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: 'dark', deviceScaleFactor: 2, hasTouch: true, isMobile: true });
  const page = await ctx.newPage();
  for (const [name, h] of shots.slice(0, 2)) {
    await page.goto(base + h); await page.waitForSelector('h1.lt'); await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(out, `${name}-phone.png`), fullPage: true });
  }
  await browser.close();
  console.log('shots in', out);
})();

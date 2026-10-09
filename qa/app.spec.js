// Browser tests for To-Do 360 against the fake-vault server (qa/run.sh starts it).
// They encode the reviewer checklist where a browser can check it: no ISO dates in visible text,
// one status pill per row, every number on Focus is a link, the Money filter really filters.
const { test, expect } = require('@playwright/test');

test.beforeEach(async ({ page, request }) => {
  await page.addInitScript(() => { try { localStorage.clear(); } catch (e) {} });
  // every spec starts from a clean decisions store
  for (const id of ['T-0101', 'T-0102', 'T-0103', 'T-1299', 'T-0006', 'T-0007']) {
    await request.post('/api/decision', { data: { kind: 'todo', id, action: 'clear' } });
    await request.post('/api/decision', { data: { kind: 'money', id, action: 'clear' } });
  }
  await request.post('/api/decision', { data: { kind: 'meeting', id: '01M4DTSVYXQQM0DXNVJ2QH3EXT', action: 'clear' } });
});

test('Focus: pinned cards, each one a link, no ISO dates', async ({ page }) => {
  await page.goto('/#/');
  await expect(page.locator('h1.lt')).toHaveText('Focus');
  const cards = page.locator('a.card.metric');
  await expect(cards).toHaveCount(8); // six pinned metrics + two highlights, all links
  for (const href of await cards.evaluateAll(els => els.map(e => e.getAttribute('href')))) expect(href).toMatch(/^#\//);
  await expect(cards.first().locator('h2')).toHaveText(/Revenue/);
  await expect(cards.first().locator('.val')).toContainText('2'); // T-0101 and T-0103 are revenue and on Abdul
  const text = await page.locator('main').innerText();
  expect(text).not.toMatch(/\d{4}-\d{2}-\d{2}/);
  expect(text).not.toContain('—'); // no em dashes in copy
});

test('To-dos: Money filter keeps only revenue to-dos and the tag explains itself', async ({ page }) => {
  await page.goto('/#/todos?owner=me&money=0');
  await expect(page.locator('h1.lt')).toHaveText('To-dos');
  await expect(page.locator('.list .row[data-id]')).toHaveCount(4);
  await expect(page.locator('.list .row[data-id] .pill.money')).toHaveCount(2); // tagged rows carry the pill
  await expect(page.locator('.row[data-id="T-0101"] .s')).toContainText('proposal, price'); // and say why, on the line
  await page.locator('#fMoney').click();
  await expect(page.locator('#fMoney')).toHaveAttribute('aria-pressed', 'true');
  const rows = page.locator('.list .row[data-id]');
  await expect(rows).toHaveCount(2);
  await expect(rows.locator('.pill.money')).toHaveCount(0); // the filter already says it; no pill repeated per row
  await expect(page.locator('.row[data-id="T-0101"] .s')).toContainText('proposal, price'); // but the why stays, for auditing
  await rows.first().hover();
  await expect(rows.first().locator('button.act.money')).toHaveText('Not revenue');
  // the Focus card deep link lands on the same filter
  await page.goto('/#/todos?owner=me&money=1');
  await expect(page.locator('#fMoney')).toHaveAttribute('aria-pressed', 'true');
});

test('To-dos: Money override is saved and survives a reload', async ({ page }) => {
  await page.goto('/#/todos?owner=me&money=0');
  const plain = page.locator('.row[data-id="T-0102"]');
  await expect(plain.locator('.pill.money')).toHaveCount(0);
  await plain.hover(); // actions appear on hover on a desktop
  await expect(plain.locator('button.act.money')).toHaveText('Revenue');
  await plain.locator('button.act.money').click();
  await expect(plain.locator('.pill.money')).toHaveCount(1);
  await expect(plain.locator('.s')).toContainText('tagged by you');
  await page.reload();
  await expect(page.locator('.row[data-id="T-0102"] .pill.money')).toHaveCount(1);
  await page.locator('.row[data-id="T-0102"]').hover();
  await expect(page.locator('.row[data-id="T-0102"] button.act.money')).toHaveText('Reset to automatic');
  await page.locator('.row[data-id="T-0102"] button.act.money').click(); // back to automatic
  await expect(page.locator('.row[data-id="T-0102"] .pill.money')).toHaveCount(0);
  // overriding a tagged one to "no" leaves a note on the row
  const tagged = page.locator('.row[data-id="T-0101"]');
  await tagged.hover();
  await tagged.locator('button.act.money').click();
  await expect(tagged.locator('.s')).toContainText('Not revenue, by you');
  await tagged.hover();
  await tagged.locator('button.act.money').click();
  await expect(tagged.locator('.pill.money')).toHaveCount(1);
});

test('To-dos: the circle marks done, one status pill, Apply counts it', async ({ page }) => {
  await page.goto('/#/todos?owner=me&money=0');
  const row = page.locator('.row[data-id="T-0101"]');
  await row.locator('button.circ').click();
  await expect(row.locator('button.circ')).toHaveAttribute('aria-pressed', 'true');
  await expect(row.locator('.pill:not(.money)')).toHaveCount(1);
  await expect(row.locator('.pill:not(.money)')).toHaveText(/Done/);
  await expect(page.locator('#apply')).toBeEnabled();
  await expect(page.locator('#apply')).toHaveText('Apply 1 to vault');
  await row.locator('button.circ').click(); // undo
  await expect(page.locator('#apply')).toBeDisabled();
  // a decided row stays on screen until the filters change, then leaves the Open list
  await row.locator('button.circ').click();
  await expect(row).toBeVisible();
  await page.locator('[data-seg="owner"] button[data-v="all"]').click();
  await expect(page.locator('.row[data-id="T-0101"]')).toHaveCount(0);
});

test('Meetings: rows open the sheet, links that are missing are disabled, Escape closes', async ({ page }) => {
  await page.goto('/#/meetings');
  await expect(page.locator('h1.lt')).toHaveText('Meetings');
  await page.locator('a.row.link', { hasText: 'Pansoft' }).first().click();
  await expect(page).toHaveURL(/#\/meeting\//);
  const sheet = page.locator('.sheet');
  await expect(sheet).toBeVisible();
  await expect(sheet.locator('h2')).toContainText('Pansoft');
  await expect(sheet.locator('.linkrow.off')).toHaveCount(0); // captured meeting: all its links exist
  await expect(sheet.locator('.sub .pill.money')).toHaveCount(1); // 3 of its 6 to-dos are about money
  await expect(sheet).toContainText('3 of 6 to-dos about money');
  await page.keyboard.press('Escape');
  await expect(page.locator('.sheet')).toHaveCount(0);
  await expect(page).toHaveURL(/#\/meetings$/);
});

test('Meetings: a skipped meeting shows the reason and no confirm control', async ({ page }) => {
  await page.goto('/#/meeting/01M4DQC6977RCF9YJJEEM9ZEWF');
  const sheet = page.locator('.sheet');
  await expect(sheet.locator('.err')).toContainText('empty capture');
  await expect(sheet.locator('[data-seg="mconf"]')).toHaveCount(0);
  await expect(sheet.locator('.linkrow.off')).toHaveCount(3); // no Airtable row, no note, no raw; the Read AI link still works
});

test('Sheet: confirming a meeting happened is saved', async ({ page }) => {
  await page.goto('/#/meeting/01M4DTSVYXQQM0DXNVJ2QH3EXT');
  await page.locator('[data-seg="mconf"] button[data-v="happened"]').click();
  await expect(page.locator('.sheet .sub .pill').first()).toHaveText('Confirmed');
  await page.locator('[data-seg="mconf"] button[data-v="happened"]').click(); // toggle off
  await expect(page.locator('.sheet .sub .pill').first()).toHaveText('Captured');
});

test('Gaps: lists the skipped and deferred meetings', async ({ page }) => {
  await page.goto('/#/gaps');
  await expect(page.locator('h1.lt')).toHaveText('Gaps');
  await expect(page.locator('main')).toContainText('Bank Loan Guy');
  await expect(page.locator('main')).toContainText('Prem Cargo');
});

test('Focus: each card opens exactly what it counted', async ({ page }) => {
  const card = title => page.locator('a.card.metric', { has: page.locator('h2', { hasText: title }) });
  await page.goto('/#/');
  await card('Older than 30 days').click();
  await expect(page.locator('h1.lt')).toHaveText('To-dos');
  await expect(page.locator('[data-seg="age"] button[aria-pressed="true"]')).toHaveText('Over 30 days');
  await expect(page.locator('.list .row[data-id]')).toHaveCount(2); // T-0006 (31 days) and T-0103 (69 days)
  await page.goto('/#/');
  await card('New this week').click();
  await expect(page.locator('[data-seg="age"] button[aria-pressed="true"]')).toHaveText('This week');
  await expect(page.locator('.list .row[data-id]')).toHaveCount(2); // T-0101, T-0102
  await page.goto('/#/');
  await card('Meetings this week').click();
  await expect(page.locator('[data-seg="mstatus"] button[aria-pressed="true"]')).toHaveText('To confirm');
});

test('Copy: your own rows read as actions, not "Abdul Rahman Janoo to"; times in Apple voice', async ({ page }) => {
  await page.goto('/#/todos?owner=me&money=0&age=all');
  const texts = await page.locator('.list .row[data-id] .t').allInnerTexts();
  for (const t of texts) expect(t).not.toMatch(/^Abdul/);
  expect(texts).toContain('Send Pradip the pricing proposal for the pilot');
  await page.goto('/#/meetings');
  await expect(page.locator('main')).toContainText('6:51 PM');
  await expect(page.locator('main')).not.toContainText('IST');
});

test('Light mode: controls sit on a visible fill, never on the page colour', async ({ browser }) => {
  const ctx = await browser.newContext({ colorScheme: 'light' });
  const page = await ctx.newPage();
  await page.goto('/#/todos?owner=me&money=0');
  const [bodyBg, searchBg, segBg] = await page.evaluate(() => [
    getComputedStyle(document.body).backgroundColor,
    getComputedStyle(document.querySelector('.search')).backgroundColor,
    getComputedStyle(document.querySelector('.seg')).backgroundColor,
  ]);
  expect(searchBg).not.toBe(bodyBg);
  expect(segBg).not.toBe(bodyBg);
  expect(searchBg).not.toBe('rgba(0, 0, 0, 0)');
  await ctx.close();
});

test('Layout: nothing overflows horizontally at phone width', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const h of ['/#/', '/#/todos?owner=all&money=0', '/#/meetings', '/#/meeting/01M4DTSVYXQQM0DXNVJ2QH3EXT']) {
    await page.goto(h);
    await expect(page.locator('h1.lt, .sheet h2').first()).toBeVisible();
    const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(over, h).toBeLessThanOrEqual(0);
  }
});

// Runs against a To-Do 360 server started on a fake vault (see run.sh) with the system Chrome.
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: __dirname,
  testMatch: /.*\.spec\.js/,
  timeout: 30000,
  fullyParallel: false,
  reporter: [['list']],
  use: {
    channel: 'chrome',
    headless: true,
    viewport: { width: 1440, height: 900 },
    baseURL: process.env.TODO360_URL || 'http://127.0.0.1:8361',
  },
});

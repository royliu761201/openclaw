const { chromium } = require("playwright");
const os = require("os");
const path = require("path");
(async () => {
  const userDataDir = path.join(os.homedir(), ".openclaw_vpn_profile");
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    channel: "chrome",
    ignoreHTTPSErrors: true,
  });
  const targetPage = context.pages().length > 0 ? context.pages()[0] : await context.newPage();
  console.log("Locating iframe...");
  const frames = targetPage.frames();
  console.log("Total frames found: " + frames.length);
  for (const frame of frames) {
    console.log("Frame Name: " + frame.name() + " | URL: " + frame.url());
    const username = frame.locator('input.input-txt[tabindex="1"]');
    if ((await username.count()) > 0) {
      console.log("FOUND USERNAME IN FRAME: " + frame.url());
      await username.fill("SKL16");
    }
  }
  await context.close();
})();

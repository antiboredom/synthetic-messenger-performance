const puppeteer = require("puppeteer");

const width = 1280;
const height = 720;
const url = "https://syntheticmessenger.labr.io/?stats=true";

async function main() {
  const launchOptions = { headless: false };

  launchOptions.args = [
    `--window-size=${width},${height}`,
    "--autoplay-policy=no-user-gesture-required",
  ];
  launchOptions.ignoreDefaultArgs = ["--enable-automation"];

  const browser = await puppeteer.launch(launchOptions);
  const page = await browser.newPage();
  await page.setViewport({
    width: width,
    height: height,
    deviceScaleFactor: 2,
  });
  page.setDefaultNavigationTimeout(30000);
  await page.goto(url);
}

main();

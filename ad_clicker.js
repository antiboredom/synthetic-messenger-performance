const puppeteer = require("puppeteer");
const fs = require("fs");
const hostname = require("os").hostname();
const bent = require("bent");
const getJSON = bent("json");
const path = require("path");

const width = 1280;
const height = 720;
const totalAgents = 1;

let assetNumber;

try {
  let hostNumber = parseInt(hostname.replace(/\D/g, ""));
  if (isNaN(hostNumber)) hostNumber = 0;
  assetNumber = hostNumber % totalAgents;
} catch (e) {
  assetNumber = 0;
}

const assetBase = `https://syntheticmessenger.s3.us-east-1.amazonaws.com/${assetNumber}/`;
console.log(assetBase);

let selectors = fs
  .readFileSync("ad_selectors.txt")
  .toString()
  .split("\n")
  .filter((s) => s.trim() != "");

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function intersects(array, obj) {
  return array.some(
    (a) =>
      a.x + a.width >= obj.x &&
      a.x <= obj.x + obj.width &&
      a.y + a.height >= obj.y &&
      a.y <= obj.y + obj.height
  );
}

async function getBBox(el) {
  return await el.evaluate((e) => {
    const { x, y, width, height } = e.getBoundingClientRect();
    return { x: x + window.scrollX, y: y + window.scrollY, width, height };
  });
}

async function getRecentArticles() {
  try {
    let results = await getJSON("http://157.245.247.231/?host=" + hostname);
    return results;
  } catch (e) {
    console.log(e);
    return [];
  }
}

async function clickAds(page, url) {
  try {
    console.log("opening", url);
    await page.goto(url);
  } catch (e) {
    console.log("could not load page");
    console.log(e);
    return false;
  }

  let adCoords = [];

  await sleep(2500);

  let elements = await page.$$(selectors.join(","));

  for (let el of elements) {
    try {
      let bbox = await getBBox(el);
      if (bbox != null && !intersects(adCoords, bbox) && bbox.width > 10 && bbox.height > 10) {
        adCoords.push(bbox);
        // await el.evaluate((e) => {
        //   e.scrollIntoView({ behavior: "smooth", block: "center" });
        // });
        // await sleep(1500);
        await el.evaluate((e) => {
          window.THESCROLLINGSOUND.play();
          e.scrollIntoView({ behavior: "smooth", block: "center" });
          let box = document.querySelector("#sams-hand");
          let bbox = e.getBoundingClientRect();
          box.style.left = bbox.x + window.scrollX + bbox.width / 2 + "px";
          box.style.top = bbox.y + window.scrollY + bbox.height / 2 + "px";
          setTimeout(() => {
            let oldBorder = e.style.outline;
            e.style.outline = "3px dashed red";
            setTimeout(() => {
              e.style.outline = oldBorder;
            }, 200);
          }, 1000);
        });
        await sleep(1000);
        await page.evaluate(() => window.THECLICKINGSOUND.play());
        await el.click({ button: "middle" });
        await sleep(500);
      }
    } catch (e) {
      console.log("could not click");
      console.log(e);
    }
    await sleep(500);
    await page.bringToFront();
    await sleep(500);
  }
  return true;
}

async function installBotHelper(page) {
  await page.evaluateOnNewDocument((assetBase) => {
    if (window !== window.parent) return;
    window.addEventListener(
      "DOMContentLoaded",
      () => {
        const box = document.createElement("video");

        box.id = "sams-hand";
        box.src = assetBase + "hand.webm";
        box.setAttribute("autoplay", "");
        box.setAttribute("muted", "");
        box.setAttribute("loop", "");

        const styleElement = document.createElement("style");

        styleElement.innerHTML = `
        #sams-hand {
          pointer-events: none;
          position: absolute;
          z-index: 100000000;
          top: 40%;
          left: 40%;
          margin-top: -110px;
          margin-left: -90px;
          width: 300px;
          transition: 1s all;
        }
      `;
        document.head.appendChild(styleElement);
        document.body.appendChild(box);

        const click = document.createElement("audio");
        click.id = "synthetic-click-sample";
        click.src = assetBase + "click.ogg";
        window.THECLICKINGSOUND = click;

        const scroll = document.createElement("audio");
        scroll.id = "synthetic-scroll-sample";
        scroll.src = assetBase + "scroll.ogg";
        window.THESCROLLINGSOUND = scroll;
      },
      false
    );
  }, assetBase);
}

async function main(urls) {
  let runForever = false;
  if (urls.length == 0) {
    urls = await getRecentArticles();
    runForever = true;
  }

  const launchOptions = { headless: false };

  const cookieExtension = path.resolve(__dirname, "cookies_ext/3.3.0_0/");

  launchOptions.args = [
    `--window-size=${width},${height}`,
    "--autoplay-policy=no-user-gesture-required",
    "--disable-extensions-except=" + cookieExtension,
    "--load-extension=" + cookieExtension,
  ];
  launchOptions.ignoreDefaultArgs = ["--enable-automation"];

  for (let url of urls) {
    const browser = await puppeteer.launch(launchOptions);
    const page = await browser.newPage();
    await page.setViewport({
      width: width,
      height: height,
      deviceScaleFactor: 2,
    });
    await installBotHelper(page); // Install Mouse Helper
    page.setDefaultNavigationTimeout(15000);
    await clickAds(page, url);
    await browser.close();
  }

  if (runForever) {
    main([]);
  }
}

try {
  let urls = process.argv.slice(2);
  main(urls);
} catch (e) {
  console.log(e);
}

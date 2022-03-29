const puppeteer = require("puppeteer");
const fs = require("fs");
const hostname = require("os").hostname();
const bent = require("bent");
const getJSON = bent("json");
const path = require("path");
const { exec } = require('child_process');

const KEY = fs.readFileSync("key.txt", { encoding: "utf8" }).trim();
const api = process.env.SYN_API || "https://syntheticmessenger.labr.io";
const max_time = 80 * 1000;

const post = bent(api, "POST", "json", 200);

const width = process.env.WIDTH ? parseInt(process.env.WIDTH) : 1280;
const height = process.env.HEIGHT ? parseInt(process.env.HEIGHT) : 720;
const totalAgents = 36;

let assetNumber;

try {
  let hostNumber = parseInt(hostname.replace(/\D/g, ""));
  if (isNaN(hostNumber)) hostNumber = 0;
  assetNumber = hostNumber % totalAgents;
} catch (e) {
  assetNumber = 0;
}

const assetBase = `https://syntheticmessenger.labr.io/synthetic_static/${assetNumber}/`;
console.log(assetBase);

let selectors = fs
  .readFileSync("ad_selectors.txt")
  .toString()
  .split("\n")
  .filter((s) => s.trim() != "");

const denylist = new RegExp(
  fs
    .readFileSync("denylist.txt", { encoding: "utf8" })
    .split("\n")
    .filter((s) => s.trim() != "")
    .join("|")
    .replace(/\./g, "[.]")
);

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
    let results = await getJSON(`${api}/articles?host=${hostname}&key=${KEY}`);
    results = results.filter((r) => !denylist.test(r));
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
    try {
      post("/visit", { host: hostname, url: url, key: KEY });
    } catch (e) {
      console.log(e);
    }
  } catch (e) {
    console.log("could not load page");
    console.log(e);
    return false;
  }

  let adCoords = [];
  let goodEls = [];

  await sleep(3500);

  let elements = await page.$$(selectors.join(","));

  for (let el of elements) {
    try {
      let bbox = await getBBox(el);
      if (bbox != null && !intersects(adCoords, bbox) && bbox.width > 10 && bbox.height > 10) {
        adCoords.push(bbox);
        goodEls.push(el);
      }
    } catch (e) {}
  }

  if (goodEls.length > 0) {
    let outname = `recordings/${new Date().getTime()}.mkv`;
    let recorderCommand = `killall -9 ffmpeg; ffmpeg -y  -f pulse -ac 2 -i default -video_size ${width}x${height} -framerate 60 -f x11grab -i :1.0+0,0 -vcodec libx264 -pix_fmt yuv420p -preset ultrafast -crf 0 -threads 0 ${outname}`;
    // let recorderCommand = `killall -9 ffmpeg; ffmpeg -y  -f pulse -ac 2 -i default -video_size ${width}x${height} -framerate 60 -f x11grab -i :1.0+0,0 -vcodec libx264 -pix_fmt yuv420p -preset veryfast -crf 15 -threads 0 ${outname}`;
    console.log('recording', outname);
    exec(recorderCommand);

    for (let el of goodEls) {
      try {
        try {
          post("/click", { host: hostname, key: KEY });
        } catch (e) {
          console.log(e);
        }

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
      } catch (e) {
        console.log("could not click");
        console.log(e);
      }
      await sleep(500);
      await page.bringToFront();
      await sleep(500);
    }
  }
  console.log('stop recording');
  exec(`killall ffmpeg`);

  return true;
}

async function installBotHelper(page) {
  await page.evaluateOnNewDocument(
    (assetBase, assetNumber) => {
      if (window !== window.parent) return;
      window.addEventListener(
        "DOMContentLoaded",
        () => {
          // const box = document.createElement("video");
          //
          // box.id = "sams-hand";
          // box.src = assetBase + "hand.webm";
          // box.setAttribute("autoplay", "");
          // box.setAttribute("muted", "");
          // box.setAttribute("loop", "");

          const box = document.createElement("img");
          box.id = "sams-hand";
          box.src = assetBase + "hand.gif";

          const styleElement = document.createElement("style");

          const adjustments = [
            [0, 0],
            [0, -80],
            [0, -80],
            [0, -60],
            [0, -20],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -20],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, 0],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -30],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -50],
            [0, -80],
            [0, -80],
            [0, -80],
            [0, -10],
            [0, -80],
            [0, -30],
            [0, -30],
          ];

          let xOff = -90;
          let yOff = -110;

          if (adjustments[assetNumber]) {
            xOff += adjustments[assetNumber][0] || 0;
            yOff += adjustments[assetNumber][1] || 0;
          }

          const w = 300;

          styleElement.innerHTML = `
        #sams-hand {
          pointer-events: none;
          position: absolute;
          z-index: 100000000;
          top: 40%;
          left: 40%;
          margin-top: ${yOff}px;
          margin-left: ${xOff}px;
          width: ${w}px;
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
    },
    assetBase,
    assetNumber
  );
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
    "--window-position=0,0",
    "--no-default-browser-check",
    "--autoplay-policy=no-user-gesture-required",
    "--disable-extensions-except=" + cookieExtension,
    "--load-extension=" + cookieExtension,
  ];
  launchOptions.ignoreDefaultArgs = ["--enable-automation"];
  let tid;

  for (let url of urls) {
    const browser = await puppeteer.launch(launchOptions);
    const page = await browser.newPage();
    await page.setViewport({
      width: width,
      height: height,
      deviceScaleFactor: 2,
    });
    await installBotHelper(page); // Install Mouse Helper
    page.setDefaultNavigationTimeout(50000);

    clearTimeout(tid);
    tid = setTimeout(async () => {
      clearTimeout(tid);
      await browser.close();
    }, max_time);

    try {
      await clickAds(page, url);
    } catch (e) {
      console.log(e);
    }
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

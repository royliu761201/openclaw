const fs = require('fs');
const https = require('https');
const crypto = require('crypto');
const { spawn } = require('child_process');

const ENV_PATH = '/Users/roy-jd/.openclaw_secrets/.env';
const CONFIG_PROD = '/Users/roy-jd/.openclaw/openclaw.json';
const CONFIG_DEV = '/Users/roy-jd/.openclaw-dev/openclaw.json';

// Simple .env parser
const env = {};
try {
  const content = fs.readFileSync(ENV_PATH, 'utf-8');
  for (const line of content.split('\n')) {
    const match = line.match(/^\s*([^#=]+)="([^"]+)"/);
    if (match) env[match[1]] = match[2];
  }
} catch (e) {
  console.error("Failed to read .env:", e.message);
  process.exit(1);
}

const CORP_ID = env.WECOM_CORP_ID;
const SECRET = env.WECOM_CORP_SECRET;
const AGENT_ID = env.WECOM_AGENT_ID;

if (!CORP_ID || !SECRET || !AGENT_ID) {
  console.error("Missing WeCom credentials in .env");
  process.exit(1);
}

// 1. Get WeCom Access Token
async function getAccessToken() {
  return new Promise((resolve, reject) => {
    https.get(`https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=${CORP_ID}&corpsecret=${SECRET}`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const body = JSON.parse(data);
        if (body.errcode === 0) resolve(body.access_token);
        else reject(new Error(`Failed to get token: ${body.errmsg}`));
      });
    }).on('error', reject);
  });
}

// 2. Set WeCom Callback URL
async function updateWeComCallback(token, newUrl, aesKey, callbackToken) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({
      agentid: parseInt(AGENT_ID, 10),
      report_location_flag: 0,
      url: newUrl,
      token: callbackToken,
      encodingaeskey: aesKey
    });

    const req = https.request({
      hostname: 'qyapi.weixin.qq.com',
      port: 443,
      path: `/cgi-bin/agent/set?access_token=${token}`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const body = JSON.parse(data);
        if (body.errcode === 0) resolve();
        else reject(new Error(`Failed to update callback API: ${body.errmsg}`));
      });
    });

    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

// 3. Update local JSON configs
function updateLocalConfigs(newUrl) {
  [CONFIG_PROD, CONFIG_DEV].forEach(file => {
    try {
      const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
      if (data.channels && data.channels.wecom && data.channels.wecom.accounts && data.channels.wecom.accounts.app) {
        data.channels.wecom.accounts.app.callbackUrl = newUrl;
        fs.writeFileSync(file, JSON.stringify(data, null, 2));
        console.log(`Updated ${file}`);
      }
    } catch (e) {
      console.error(`Failed to update ${file}:`, e.message);
    }
  });
}

// Main: Launch Cloudflared and parse its output
console.log("Starting cloudflared tunnel...");
const cf = spawn('/opt/homebrew/bin/cloudflared', ['tunnel', '--url', 'http://127.0.0.1:19001']);

cf.stderr.on('data', async (data) => {
  const line = data.toString();
  process.stdout.write(line);
  
  const match = line.match(/https:\/\/[a-z0-9-]+\.trycloudflare\.com/);
  if (match) {
    const baseUrl = match[0];
    const fullCallbackUrl = `${baseUrl}/wecom/app`;
    console.log(`\n=== Found new Cloudflare URL: ${fullCallbackUrl} ===\n`);
    
    try {
      updateLocalConfigs(fullCallbackUrl);
      console.log("Getting WeCom Access Token...");
      const token = await getAccessToken();
      console.log("Updating WeCom Server...");
      await updateWeComCallback(token, fullCallbackUrl, env.WECOM_ENCODING_AES_KEY, env.WECOM_TOKEN);
      console.log("\n✅ Successfully synced new Cloudflare URL to WeCom backend!");
    } catch (err) {
      console.error("❌ Sync failed:", err.message);
    }
  }
});

cf.on('close', (code) => {
  console.log(`cloudflared exited with code ${code}`);
});

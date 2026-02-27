const fs = require('fs');
const file = '/Users/roy-jd/.openclaw-dev/openclaw.json';
const data = JSON.parse(fs.readFileSync(file));
data.channels = data.channels || {};
data.channels.wecom = {
  enabled: true,
  mode: "app",
  defaultAccount: "app",
  allowFrom: ["*"],
  accounts: {
    app: {
      mode: "app",
      webhookPath: "/wecom/app",
      corpId: "${WECOM_CORPID}",
      corpSecret: "${WECOM_SECRET}",
      agentId: 1000003,
      callbackToken: "${WECOM_TOKEN}",
      callbackAesKey: "${WECOM_ENCODING_AES_KEY}"
    }
  }
};
data.plugins = data.plugins || {};
data.plugins.entries = data.plugins.entries || {};
data.plugins.entries["@marshulll/openclaw-wecom"] = { enabled: true };
fs.writeFileSync(file, JSON.stringify(data, null, 2));

const fs = require("fs");
const path = require("path");

const prodPath = path.join(process.env.HOME, ".openclaw/openclaw.json");
const devPath = path.join(process.env.HOME, ".openclaw-dev/openclaw.json");

const prodConfig = JSON.parse(fs.readFileSync(prodPath, "utf8"));
const devConfig = JSON.parse(fs.readFileSync(devPath, "utf8"));

// Deep merge strategy: Dev config takes precedence for gateway/auth, Prod config provides everything else
const merged = {
  ...prodConfig,
  ...devConfig, // Dev base overrides Prod base
  gateway: {
    ...prodConfig.gateway,
    ...devConfig.gateway, // Dev gateway settings override Prod gateway settings
  },
  channels: {
    ...prodConfig.channels,
    ...devConfig.channels, // If Dev has specific channels set up, keep them; otherwise inherit Prod
  },
  agents: {
    ...prodConfig.agents,
    ...devConfig.agents,
  },
  plugins: {
    ...prodConfig.plugins,
    ...devConfig.plugins,
  },
};

fs.writeFileSync(devPath, JSON.stringify(merged, null, 2));
console.log("Successfully merged production configuration into dev profile.");

import "./paths-DVBShlw6.js";
import { R as theme, c as defaultRuntime } from "./subsystem-DHfJG4gk.js";
import "./utils-BtIMES3N.js";
import "./pi-embedded-helpers-BubZUNx-.js";
import "./exec-4V5EwH-r.js";
import "./agent-scope-D_p2LOiK.js";
import "./model-selection-CTKoRqDI.js";
import "./github-copilot-token-CiF5Iyi2.js";
import "./boolean-BgXe2hyu.js";
import "./env-BUuSkE19.js";
import "./config-CmDYseI1.js";
import "./manifest-registry-jeAPx6AW.js";
import "./plugins-BvNdouUY.js";
import "./sandbox-4W8S1yx4.js";
import "./chrome-BtcIWBGj.js";
import "./skills-Dz15dAM4.js";
import "./routes-onyxaWpE.js";
import "./server-context-B5b9OM_w.js";
import "./message-channel-CTtrEkmW.js";
import "./logging-fywhKCmE.js";
import "./accounts-54zZMYCo.js";
import "./paths-DdKf4lHp.js";
import "./redact-BRsnXqwD.js";
import "./tool-display-kpW5Hg2z.js";
import "./commands-registry-DwM7YArf.js";
import "./client-_wavkSyB.js";
import "./call-tAGBQPmT.js";
import { t as formatDocsLink } from "./links-AVB88xxH.js";
import { t as parseTimeoutMs } from "./parse-timeout-D1XX_zN_.js";
import { t as runTui } from "./tui-DRh73jR5.js";

//#region src/cli/tui-cli.ts
function registerTuiCli(program) {
	program.command("tui").description("Open a terminal UI connected to the Gateway").option("--url <url>", "Gateway WebSocket URL (defaults to gateway.remote.url when configured)").option("--token <token>", "Gateway token (if required)").option("--password <password>", "Gateway password (if required)").option("--session <key>", "Session key (default: \"main\", or \"global\" when scope is global)").option("--deliver", "Deliver assistant replies", false).option("--thinking <level>", "Thinking level override").option("--message <text>", "Send an initial message after connecting").option("--timeout-ms <ms>", "Agent timeout in ms (defaults to agents.defaults.timeoutSeconds)").option("--history-limit <n>", "History entries to load", "200").addHelpText("after", () => `\n${theme.muted("Docs:")} ${formatDocsLink("/cli/tui", "docs.openclaw.ai/cli/tui")}\n`).action(async (opts) => {
		try {
			const timeoutMs = parseTimeoutMs(opts.timeoutMs);
			if (opts.timeoutMs !== void 0 && timeoutMs === void 0) defaultRuntime.error(`warning: invalid --timeout-ms "${String(opts.timeoutMs)}"; ignoring`);
			const historyLimit = Number.parseInt(String(opts.historyLimit ?? "200"), 10);
			await runTui({
				url: opts.url,
				token: opts.token,
				password: opts.password,
				session: opts.session,
				deliver: Boolean(opts.deliver),
				thinking: opts.thinking,
				message: opts.message,
				timeoutMs,
				historyLimit: Number.isNaN(historyLimit) ? void 0 : historyLimit
			});
		} catch (err) {
			defaultRuntime.error(String(err));
			defaultRuntime.exit(1);
		}
	});
}

//#endregion
export { registerTuiCli };
import { A as theme, p as defaultRuntime } from "./entry.js";
import "./auth-profiles-DIgZUMSR.js";
import "./utils-BLJAc3ZV.js";
import "./exec-CPPvAI1K.js";
import "./agent-scope-DpnW8E9V.js";
import "./github-copilot-token-C9W4SY9o.js";
import "./config-BDCbZ1IN.js";
import "./manifest-registry-CVsqjgX0.js";
import "./server-context-CK21ypXp.js";
import "./chrome-xx1k4_sV.js";
import "./client-CGJjaVvZ.js";
import "./call-VglkjpoM.js";
import "./message-channel-DWcu72r7.js";
import { t as formatDocsLink } from "./links-DpxpaKe1.js";
import "./plugins-haUgxMzs.js";
import "./logging-D-Jq2wIo.js";
import "./accounts-Bvh0DFxS.js";
import "./paths-BZK4Ct0I.js";
import "./redact-UvkXqguc.js";
import "./routes-BJ0DSRhx.js";
import "./pi-embedded-helpers-Cc8iXajw.js";
import "./sandbox-BdqugcyI.js";
import "./commands-registry-B1zZgkWt.js";
import "./skills-CE7by2IF.js";
import "./tool-display-DbdMQFZx.js";
import { t as parseTimeoutMs } from "./parse-timeout-D1XX_zN_.js";
import { t as runTui } from "./tui-B27IhTgZ.js";

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
import "./paths-DVBShlw6.js";
import { E as danger, R as theme, c as defaultRuntime } from "./subsystem-DHfJG4gk.js";
import "./utils-BtIMES3N.js";
import "./exec-4V5EwH-r.js";
import "./agent-scope-D_p2LOiK.js";
import { gt as listProfilesForProvider, xt as ensureAuthProfileStore } from "./model-selection-CTKoRqDI.js";
import "./github-copilot-token-CiF5Iyi2.js";
import "./boolean-BgXe2hyu.js";
import "./env-BUuSkE19.js";
import "./config-C4SM4a2M.js";
import "./manifest-registry-jeAPx6AW.js";
import "./message-channel-CTtrEkmW.js";
import "./client-_wavkSyB.js";
import "./call-sVHdmtS8.js";
import { t as formatDocsLink } from "./links-AVB88xxH.js";
import "./progress-DZb6yPcJ.js";
import { n as callGatewayFromCli, t as addGatewayClientOptions } from "./gateway-rpc-DLFF01Ft.js";
import path from "node:path";
import fs from "node:fs/promises";

//#region src/agents/pi-auth-json.ts
async function readAuthJson(filePath) {
	try {
		const raw = await fs.readFile(filePath, "utf8");
		const parsed = JSON.parse(raw);
		if (!parsed || typeof parsed !== "object") return {};
		return parsed;
	} catch {
		return {};
	}
}
/**
* pi-coding-agent's ModelRegistry/AuthStorage expects OAuth credentials in auth.json.
*
* OpenClaw stores OAuth credentials in auth-profiles.json instead. This helper
* bridges a subset of credentials into agentDir/auth.json so pi-coding-agent can
* (a) consider the provider authenticated and (b) include built-in models in its
* registry/catalog output.
*
* Currently used for openai-codex.
*/
async function ensurePiAuthJsonFromAuthProfiles(agentDir) {
	const store = ensureAuthProfileStore(agentDir, { allowKeychainPrompt: false });
	const codexProfiles = listProfilesForProvider(store, "openai-codex");
	if (codexProfiles.length === 0) return {
		wrote: false,
		authPath: path.join(agentDir, "auth.json")
	};
	const profileId = codexProfiles[0];
	const cred = profileId ? store.profiles[profileId] : void 0;
	if (!cred || cred.type !== "oauth") return {
		wrote: false,
		authPath: path.join(agentDir, "auth.json")
	};
	const accessRaw = cred.access;
	const refreshRaw = cred.refresh;
	const expiresRaw = cred.expires;
	const access = typeof accessRaw === "string" ? accessRaw.trim() : "";
	const refresh = typeof refreshRaw === "string" ? refreshRaw.trim() : "";
	const expires = typeof expiresRaw === "number" ? expiresRaw : NaN;
	if (!access || !refresh || !Number.isFinite(expires) || expires <= 0) return {
		wrote: false,
		authPath: path.join(agentDir, "auth.json")
	};
	const authPath = path.join(agentDir, "auth.json");
	const next = await readAuthJson(authPath);
	const existing = next["openai-codex"];
	const desired = {
		type: "oauth",
		access,
		refresh,
		expires
	};
	if (existing && typeof existing === "object" && existing.type === "oauth" && existing.access === access && existing.refresh === refresh && existing.expires === expires) return {
		wrote: false,
		authPath
	};
	next["openai-codex"] = desired;
	await fs.mkdir(agentDir, {
		recursive: true,
		mode: 448
	});
	await fs.writeFile(authPath, `${JSON.stringify(next, null, 2)}\n`, { mode: 384 });
	return {
		wrote: true,
		authPath
	};
}

//#endregion
//#region src/cli/system-cli.ts
const normalizeWakeMode = (raw) => {
	const mode = typeof raw === "string" ? raw.trim() : "";
	if (!mode) return "next-heartbeat";
	if (mode === "now" || mode === "next-heartbeat") return mode;
	throw new Error("--mode must be now or next-heartbeat");
};
function registerSystemCli(program) {
	const system = program.command("system").description("System tools (events, heartbeat, presence)").addHelpText("after", () => `\n${theme.muted("Docs:")} ${formatDocsLink("/cli/system", "docs.openclaw.ai/cli/system")}\n`);
	addGatewayClientOptions(system.command("event").description("Enqueue a system event and optionally trigger a heartbeat").requiredOption("--text <text>", "System event text").option("--mode <mode>", "Wake mode (now|next-heartbeat)", "next-heartbeat").option("--json", "Output JSON", false)).action(async (opts) => {
		try {
			const text = typeof opts.text === "string" ? opts.text.trim() : "";
			if (!text) throw new Error("--text is required");
			const result = await callGatewayFromCli("wake", opts, {
				mode: normalizeWakeMode(opts.mode),
				text
			}, { expectFinal: false });
			if (opts.json) defaultRuntime.log(JSON.stringify(result, null, 2));
			else defaultRuntime.log("ok");
		} catch (err) {
			defaultRuntime.error(danger(String(err)));
			defaultRuntime.exit(1);
		}
	});
	const heartbeat = system.command("heartbeat").description("Heartbeat controls");
	addGatewayClientOptions(heartbeat.command("last").description("Show the last heartbeat event").option("--json", "Output JSON", false)).action(async (opts) => {
		try {
			const result = await callGatewayFromCli("last-heartbeat", opts, void 0, { expectFinal: false });
			defaultRuntime.log(JSON.stringify(result, null, 2));
		} catch (err) {
			defaultRuntime.error(danger(String(err)));
			defaultRuntime.exit(1);
		}
	});
	addGatewayClientOptions(heartbeat.command("enable").description("Enable heartbeats").option("--json", "Output JSON", false)).action(async (opts) => {
		try {
			const result = await callGatewayFromCli("set-heartbeats", opts, { enabled: true }, { expectFinal: false });
			defaultRuntime.log(JSON.stringify(result, null, 2));
		} catch (err) {
			defaultRuntime.error(danger(String(err)));
			defaultRuntime.exit(1);
		}
	});
	addGatewayClientOptions(heartbeat.command("disable").description("Disable heartbeats").option("--json", "Output JSON", false)).action(async (opts) => {
		try {
			const result = await callGatewayFromCli("set-heartbeats", opts, { enabled: false }, { expectFinal: false });
			defaultRuntime.log(JSON.stringify(result, null, 2));
		} catch (err) {
			defaultRuntime.error(danger(String(err)));
			defaultRuntime.exit(1);
		}
	});
	addGatewayClientOptions(system.command("presence").description("List system presence entries").option("--json", "Output JSON", false)).action(async (opts) => {
		try {
			const result = await callGatewayFromCli("system-presence", opts, void 0, { expectFinal: false });
			defaultRuntime.log(JSON.stringify(result, null, 2));
		} catch (err) {
			defaultRuntime.error(danger(String(err)));
			defaultRuntime.exit(1);
		}
	});
}

//#endregion
export { registerSystemCli, ensurePiAuthJsonFromAuthProfiles as t };
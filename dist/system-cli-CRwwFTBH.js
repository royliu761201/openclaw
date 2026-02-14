import { A as theme, p as defaultRuntime, v as danger } from "./entry.js";
import { p as listProfilesForProvider, v as ensureAuthProfileStore } from "./auth-profiles-DIgZUMSR.js";
import "./utils-BLJAc3ZV.js";
import "./exec-CPPvAI1K.js";
import "./agent-scope-DpnW8E9V.js";
import "./github-copilot-token-C9W4SY9o.js";
import "./config-TOMBPbi7.js";
import "./manifest-registry-CVsqjgX0.js";
import "./client-CGJjaVvZ.js";
import "./call-DHpd82Uy.js";
import "./message-channel-DWcu72r7.js";
import { t as formatDocsLink } from "./links-DpxpaKe1.js";
import "./progress-COHv-uNT.js";
import { n as callGatewayFromCli, t as addGatewayClientOptions } from "./gateway-rpc-CIxmDw7b.js";
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
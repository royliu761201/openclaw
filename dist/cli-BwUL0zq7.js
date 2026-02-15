import { o as createSubsystemLogger } from "./entry.js";
import "./auth-profiles-DIgZUMSR.js";
import "./utils-BLJAc3ZV.js";
import "./exec-CPPvAI1K.js";
import { c as resolveDefaultAgentId, s as resolveAgentWorkspaceDir } from "./agent-scope-DpnW8E9V.js";
import "./github-copilot-token-C9W4SY9o.js";
import "./pi-model-discovery-EhM2JAQo.js";
import { i as loadConfig } from "./config-BDCbZ1IN.js";
import "./manifest-registry-CVsqjgX0.js";
import "./server-context-CK21ypXp.js";
import "./chrome-xx1k4_sV.js";
import "./auth-DS2aFsxs.js";
import "./control-auth-BnzxSJhX.js";
import "./control-service-BFxy3F9r.js";
import "./client-CGJjaVvZ.js";
import "./call-VglkjpoM.js";
import "./message-channel-DWcu72r7.js";
import "./links-DpxpaKe1.js";
import "./plugins-haUgxMzs.js";
import "./logging-D-Jq2wIo.js";
import "./accounts-Bvh0DFxS.js";
import { t as loadOpenClawPlugins } from "./loader-CbLFPWQb.js";
import "./progress-COHv-uNT.js";
import "./prompt-style-Cf1r1L6k.js";
import "./deliver-D-KdthLP.js";
import "./manager-vyH-CKwM.js";
import "./paths-BZK4Ct0I.js";
import "./sqlite-2UsPaJz5.js";
import "./redact-UvkXqguc.js";
import "./routes-BJ0DSRhx.js";
import "./pi-embedded-helpers-Cc8iXajw.js";
import "./fetch-CVrZ5Q28.js";
import "./sandbox-BdqugcyI.js";
import "./commands-registry-B1zZgkWt.js";
import "./wsl-DK0PnBE-.js";
import "./skills-CE7by2IF.js";
import "./image-BzXMyBD7.js";
import "./nodes-screen-CVL9363A.js";
import "./tool-display-DbdMQFZx.js";
import "./channel-selection-DnfoTVpw.js";
import "./session-cost-usage-B-tyjp76.js";
import "./runner-CGRzVdkN.js";
import "./commands-D2PtfySh.js";
import "./pairing-store--uxwA3DJ.js";
import "./login-qr-8A7a_2ZX.js";
import "./pairing-labels-Cqwk2iBH.js";

//#region src/plugins/cli.ts
const log = createSubsystemLogger("plugins");
function registerPluginCliCommands(program, cfg) {
	const config = cfg ?? loadConfig();
	const workspaceDir = resolveAgentWorkspaceDir(config, resolveDefaultAgentId(config));
	const logger = {
		info: (msg) => log.info(msg),
		warn: (msg) => log.warn(msg),
		error: (msg) => log.error(msg),
		debug: (msg) => log.debug(msg)
	};
	const registry = loadOpenClawPlugins({
		config,
		workspaceDir,
		logger
	});
	const existingCommands = new Set(program.commands.map((cmd) => cmd.name()));
	for (const entry of registry.cliRegistrars) {
		if (entry.commands.length > 0) {
			const overlaps = entry.commands.filter((command) => existingCommands.has(command));
			if (overlaps.length > 0) {
				log.debug(`plugin CLI register skipped (${entry.pluginId}): command already registered (${overlaps.join(", ")})`);
				continue;
			}
		}
		try {
			const result = entry.register({
				program,
				config,
				workspaceDir,
				logger
			});
			if (result && typeof result.then === "function") result.catch((err) => {
				log.warn(`plugin CLI register failed (${entry.pluginId}): ${String(err)}`);
			});
			for (const command of entry.commands) existingCommands.add(command);
		} catch (err) {
			log.warn(`plugin CLI register failed (${entry.pluginId}): ${String(err)}`);
		}
	}
}

//#endregion
export { registerPluginCliCommands };
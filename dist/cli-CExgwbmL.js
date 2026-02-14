import "./paths-DVBShlw6.js";
import { t as createSubsystemLogger } from "./subsystem-DHfJG4gk.js";
import "./utils-BtIMES3N.js";
import "./pi-embedded-helpers-E79zFwcx.js";
import { ut as loadOpenClawPlugins } from "./reply-Bbu_CAUy.js";
import "./exec-4V5EwH-r.js";
import { c as resolveDefaultAgentId, s as resolveAgentWorkspaceDir } from "./agent-scope-D_p2LOiK.js";
import "./model-selection-CTKoRqDI.js";
import "./github-copilot-token-CiF5Iyi2.js";
import "./boolean-BgXe2hyu.js";
import "./env-BUuSkE19.js";
import { i as loadConfig } from "./config-C4SM4a2M.js";
import "./manifest-registry-jeAPx6AW.js";
import "./plugins-BvNdouUY.js";
import "./sandbox-Cw1iP13R.js";
import "./runner-BdodCVTB.js";
import "./image-BtSrQl2-.js";
import "./pi-model-discovery-EwKVHlZB.js";
import "./chrome-BtcIWBGj.js";
import "./skills-Dz15dAM4.js";
import "./routes-BF4kTHtn.js";
import "./server-context-B5b9OM_w.js";
import "./message-channel-CTtrEkmW.js";
import "./logging-fywhKCmE.js";
import "./accounts-54zZMYCo.js";
import "./paths-DdKf4lHp.js";
import "./redact-BRsnXqwD.js";
import "./tool-display-kpW5Hg2z.js";
import "./fetch-C_blAHvl.js";
import "./deliver-CAfUcf-u.js";
import "./dispatcher-EOnzuPVJ.js";
import "./manager-6brp4Eij.js";
import "./sqlite-CASnHrgX.js";
import "./commands-registry-Dmp2yCd7.js";
import "./client-_wavkSyB.js";
import "./call-sVHdmtS8.js";
import "./login-qr-DYqSl5EK.js";
import "./pairing-store-l1Pz_Ooh.js";
import "./links-AVB88xxH.js";
import "./progress-DZb6yPcJ.js";
import "./pi-tools.policy-Bp3e8-M8.js";
import "./prompt-style-lSlXMhsd.js";
import "./pairing-labels-XkKxEWhj.js";
import "./session-cost-usage-BYUb7fov.js";
import "./nodes-screen-DsHJIN2I.js";
import "./auth-DWxmgKrO.js";
import "./control-auth-CrFfND_r.js";
import "./control-service-DmpGiZ3m.js";
import "./channel-selection-C3umWMS0.js";

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
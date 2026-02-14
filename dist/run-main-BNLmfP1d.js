import { c as enableConsoleCapture, i as normalizeEnv, n as isTruthyEnvValue, p as defaultRuntime } from "./entry.js";
import "./auth-profiles-DIgZUMSR.js";
import "./utils-BLJAc3ZV.js";
import "./exec-CPPvAI1K.js";
import "./agent-scope-DpnW8E9V.js";
import "./github-copilot-token-C9W4SY9o.js";
import "./pi-model-discovery-EhM2JAQo.js";
import { F as loadDotEnv, P as VERSION } from "./config-TOMBPbi7.js";
import "./manifest-registry-CVsqjgX0.js";
import "./server-context-CK21ypXp.js";
import "./chrome-xx1k4_sV.js";
import "./auth-DS2aFsxs.js";
import "./control-auth-hoobpi5P.js";
import { r as formatUncaughtError } from "./errors-Cojm0Kl7.js";
import "./control-service-CktG7E9N.js";
import { t as ensureOpenClawCliOnPath } from "./path-env-OJAyUeWW.js";
import "./client-CGJjaVvZ.js";
import "./call-DHpd82Uy.js";
import "./message-channel-DWcu72r7.js";
import "./links-DpxpaKe1.js";
import "./plugin-auto-enable-Dx3c94r9.js";
import "./plugins-haUgxMzs.js";
import "./logging-D-Jq2wIo.js";
import "./accounts-Bvh0DFxS.js";
import "./loader-CFDxWA8T.js";
import "./progress-COHv-uNT.js";
import "./prompt-style-Cf1r1L6k.js";
import "./note-Duiadw1g.js";
import "./clack-prompter-DpuKn_Uy.js";
import "./onboard-channels-DizOwdL0.js";
import "./archive-aSMUcOc6.js";
import "./skill-scanner-BrGkh5K7.js";
import "./installs-BMQzPk7O.js";
import "./deliver-CXpWsQgI.js";
import "./manager-vyH-CKwM.js";
import "./paths-BZK4Ct0I.js";
import "./sqlite-2UsPaJz5.js";
import "./redact-UvkXqguc.js";
import "./routes-CzAxZT1e.js";
import "./pi-embedded-helpers-ghzIlEm5.js";
import "./fetch-CoFYPd54.js";
import "./sandbox-udEhG_lJ.js";
import "./commands-registry-Bvs8qWYM.js";
import "./wsl-DV_TdlKm.js";
import "./skills-CE7by2IF.js";
import "./image-D9vyfSoU.js";
import "./nodes-screen-CVL9363A.js";
import "./tool-display-DbdMQFZx.js";
import "./channel-selection-DnfoTVpw.js";
import "./session-cost-usage-B-tyjp76.js";
import { m as installUnhandledRejectionHandler } from "./runner-Deyi6U-h.js";
import "./commands-DWjDFiEa.js";
import "./pairing-store--uxwA3DJ.js";
import "./login-qr-BecYP_on.js";
import "./pairing-labels-Cqwk2iBH.js";
import "./channels-status-issues-CPoNprEl.js";
import { n as ensurePluginRegistryLoaded } from "./command-options-Bbt4zcNn.js";
import { a as getCommandPath, c as getPrimaryCommand, d as hasHelpOrVersion } from "./register.subclis-CiLQGJuX.js";
import "./completion-cli-DNVbKWYJ.js";
import "./gateway-rpc-CIxmDw7b.js";
import "./deps-DRcCHM3p.js";
import { h as assertSupportedRuntime } from "./daemon-runtime-DV9m8zhQ.js";
import "./service-CRQPieXI.js";
import "./systemd-BNvgdkdy.js";
import "./service-audit-tpVP1jqw.js";
import "./table-Bvka_vkc.js";
import "./widearea-dns-C4RnIR9O.js";
import "./audit-DRmtU2Qf.js";
import "./onboard-skills-BPGCV9QT.js";
import "./health-format-dUH-zMGm.js";
import "./update-runner-Bnjr5SLD.js";
import "./openai-codex-oauth-DMXNyz6W.js";
import "./logging-B3KnAryz.js";
import "./hooks-status-BbIz0zmm.js";
import "./status-OdJvpw4M.js";
import "./skills-status-B99Us6yS.js";
import "./tui-Chk5TObG.js";
import "./agent-BikI6wAC.js";
import "./node-service-n1d2hMXt.js";
import "./auth-health-BaJwObbE.js";
import { a as findRoutedCommand, n as emitCliBanner, t as ensureConfigReady } from "./config-guard-DItbRvq1.js";
import "./help-format-Cd5PLwXe.js";
import "./configure-BDb6zkLM.js";
import "./systemd-linger-CBiLPxts.js";
import "./doctor-C3is_NPX.js";
import path from "node:path";
import process$1 from "node:process";
import fs from "node:fs";
import { fileURLToPath } from "node:url";

//#region src/cli/route.ts
async function prepareRoutedCommand(params) {
	emitCliBanner(VERSION, { argv: params.argv });
	await ensureConfigReady({
		runtime: defaultRuntime,
		commandPath: params.commandPath
	});
	if (params.loadPlugins) ensurePluginRegistryLoaded();
}
async function tryRouteCli(argv) {
	if (isTruthyEnvValue(process.env.OPENCLAW_DISABLE_ROUTE_FIRST)) return false;
	if (hasHelpOrVersion(argv)) return false;
	const path = getCommandPath(argv, 2);
	if (!path[0]) return false;
	const route = findRoutedCommand(path);
	if (!route) return false;
	await prepareRoutedCommand({
		argv,
		commandPath: path,
		loadPlugins: route.loadPlugins
	});
	return route.run(argv);
}

//#endregion
//#region src/cli/run-main.ts
function rewriteUpdateFlagArgv(argv) {
	const index = argv.indexOf("--update");
	if (index === -1) return argv;
	const next = [...argv];
	next.splice(index, 1, "update");
	return next;
}
async function runCli(argv = process$1.argv) {
	const normalizedArgv = stripWindowsNodeExec(argv);
	loadDotEnv({ quiet: true });
	normalizeEnv();
	ensureOpenClawCliOnPath();
	assertSupportedRuntime();
	if (await tryRouteCli(normalizedArgv)) return;
	enableConsoleCapture();
	const { buildProgram } = await import("./program-C7bSxeqU.js");
	const program = buildProgram();
	installUnhandledRejectionHandler();
	process$1.on("uncaughtException", (error) => {
		console.error("[openclaw] Uncaught exception:", formatUncaughtError(error));
		process$1.exit(1);
	});
	const parseArgv = rewriteUpdateFlagArgv(normalizedArgv);
	const primary = getPrimaryCommand(parseArgv);
	if (primary) {
		const { registerSubCliByName } = await import("./register.subclis-CiLQGJuX.js").then((n) => n.i);
		await registerSubCliByName(program, primary);
	}
	if (!(!primary && hasHelpOrVersion(parseArgv))) {
		const { registerPluginCliCommands } = await import("./cli-BQQTWeOs.js");
		const { loadConfig } = await import("./config-TOMBPbi7.js").then((n) => n.t);
		registerPluginCliCommands(program, loadConfig());
	}
	await program.parseAsync(parseArgv);
}
function stripWindowsNodeExec(argv) {
	if (process$1.platform !== "win32") return argv;
	const stripControlChars = (value) => {
		let out = "";
		for (let i = 0; i < value.length; i += 1) {
			const code = value.charCodeAt(i);
			if (code >= 32 && code !== 127) out += value[i];
		}
		return out;
	};
	const normalizeArg = (value) => stripControlChars(value).replace(/^['"]+|['"]+$/g, "").trim();
	const normalizeCandidate = (value) => normalizeArg(value).replace(/^\\\\\\?\\/, "");
	const execPath = normalizeCandidate(process$1.execPath);
	const execPathLower = execPath.toLowerCase();
	const execBase = path.basename(execPath).toLowerCase();
	const isExecPath = (value) => {
		if (!value) return false;
		const normalized = normalizeCandidate(value);
		if (!normalized) return false;
		const lower = normalized.toLowerCase();
		return lower === execPathLower || path.basename(lower) === execBase || lower.endsWith("\\node.exe") || lower.endsWith("/node.exe") || lower.includes("node.exe") || path.basename(lower) === "node.exe" && fs.existsSync(normalized);
	};
	const filtered = argv.filter((arg, index) => index === 0 || !isExecPath(arg));
	if (filtered.length < 3) return filtered;
	const cleaned = [...filtered];
	if (isExecPath(cleaned[1])) cleaned.splice(1, 1);
	if (isExecPath(cleaned[2])) cleaned.splice(2, 1);
	return cleaned;
}

//#endregion
export { runCli };
import { A as theme, k as isRich, n as isTruthyEnvValue, p as defaultRuntime, w as setVerbose } from "./entry.js";
import "./auth-profiles-DIgZUMSR.js";
import { n as replaceCliName, r as resolveCliName } from "./command-format-Bxe0mWee.js";
import "./utils-BLJAc3ZV.js";
import "./exec-CPPvAI1K.js";
import "./agent-scope-DpnW8E9V.js";
import "./github-copilot-token-C9W4SY9o.js";
import "./pi-model-discovery-EhM2JAQo.js";
import { P as VERSION } from "./config-TOMBPbi7.js";
import "./manifest-registry-CVsqjgX0.js";
import "./server-context-CK21ypXp.js";
import "./chrome-xx1k4_sV.js";
import "./auth-DS2aFsxs.js";
import "./control-auth-hoobpi5P.js";
import "./control-service-CktG7E9N.js";
import "./client-CGJjaVvZ.js";
import "./call-DHpd82Uy.js";
import "./message-channel-DWcu72r7.js";
import { t as formatDocsLink } from "./links-DpxpaKe1.js";
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
import "./runner-Deyi6U-h.js";
import "./commands-DWjDFiEa.js";
import "./pairing-store--uxwA3DJ.js";
import "./login-qr-BecYP_on.js";
import "./pairing-labels-Cqwk2iBH.js";
import "./channels-status-issues-CPoNprEl.js";
import { n as ensurePluginRegistryLoaded } from "./command-options-Bbt4zcNn.js";
import { n as resolveCliChannelOptions } from "./channel-options-1DRYLvEd.js";
import { a as getCommandPath, d as hasHelpOrVersion, l as getVerboseFlag } from "./register.subclis-CiLQGJuX.js";
import "./completion-cli-DNVbKWYJ.js";
import "./gateway-rpc-CIxmDw7b.js";
import "./deps-DRcCHM3p.js";
import "./daemon-runtime-DV9m8zhQ.js";
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
import { t as forceFreePort } from "./ports-D5ftfLU7.js";
import "./auth-health-BaJwObbE.js";
import { i as hasEmittedCliBanner, n as emitCliBanner, o as registerProgramCommands, r as formatCliBannerLine, t as ensureConfigReady } from "./config-guard-DItbRvq1.js";
import "./help-format-Cd5PLwXe.js";
import "./configure-BDb6zkLM.js";
import "./systemd-linger-CBiLPxts.js";
import "./doctor-C3is_NPX.js";
import { Command } from "commander";

//#region src/cli/program/context.ts
function createProgramContext() {
	const channelOptions = resolveCliChannelOptions();
	return {
		programVersion: VERSION,
		channelOptions,
		messageChannelOptions: channelOptions.join("|"),
		agentChannelOptions: ["last", ...channelOptions].join("|")
	};
}

//#endregion
//#region src/cli/program/help.ts
const CLI_NAME = resolveCliName();
const EXAMPLES = [
	["openclaw channels login --verbose", "Link personal WhatsApp Web and show QR + connection logs."],
	["openclaw message send --target +15555550123 --message \"Hi\" --json", "Send via your web session and print JSON result."],
	["openclaw gateway --port 18789", "Run the WebSocket Gateway locally."],
	["openclaw --dev gateway", "Run a dev Gateway (isolated state/config) on ws://127.0.0.1:19001."],
	["openclaw gateway --force", "Kill anything bound to the default gateway port, then start it."],
	["openclaw gateway ...", "Gateway control via WebSocket."],
	["openclaw agent --to +15555550123 --message \"Run summary\" --deliver", "Talk directly to the agent using the Gateway; optionally send the WhatsApp reply."],
	["openclaw message send --channel telegram --target @mychat --message \"Hi\"", "Send via your Telegram bot."]
];
function configureProgramHelp(program, ctx) {
	program.name(CLI_NAME).description("").version(ctx.programVersion).option("--dev", "Dev profile: isolate state under ~/.openclaw-dev, default gateway port 19001, and shift derived ports (browser/canvas)").option("--profile <name>", "Use a named profile (isolates OPENCLAW_STATE_DIR/OPENCLAW_CONFIG_PATH under ~/.openclaw-<name>)");
	program.option("--no-color", "Disable ANSI colors", false);
	program.configureHelp({
		sortSubcommands: true,
		sortOptions: true,
		optionTerm: (option) => theme.option(option.flags),
		subcommandTerm: (cmd) => theme.command(cmd.name())
	});
	program.configureOutput({
		writeOut: (str) => {
			const colored = str.replace(/^Usage:/gm, theme.heading("Usage:")).replace(/^Options:/gm, theme.heading("Options:")).replace(/^Commands:/gm, theme.heading("Commands:"));
			process.stdout.write(colored);
		},
		writeErr: (str) => process.stderr.write(str),
		outputError: (str, write) => write(theme.error(str))
	});
	if (process.argv.includes("-V") || process.argv.includes("--version") || process.argv.includes("-v")) {
		console.log(ctx.programVersion);
		process.exit(0);
	}
	program.addHelpText("beforeAll", () => {
		if (hasEmittedCliBanner()) return "";
		const rich = isRich();
		return `\n${formatCliBannerLine(ctx.programVersion, { richTty: rich })}\n`;
	});
	const fmtExamples = EXAMPLES.map(([cmd, desc]) => `  ${theme.command(replaceCliName(cmd, CLI_NAME))}\n    ${theme.muted(desc)}`).join("\n");
	program.addHelpText("afterAll", ({ command }) => {
		if (command !== program) return "";
		const docs = formatDocsLink("/cli", "docs.openclaw.ai/cli");
		return `\n${theme.heading("Examples:")}\n${fmtExamples}\n\n${theme.muted("Docs:")} ${docs}\n`;
	});
}

//#endregion
//#region src/cli/program/preaction.ts
function setProcessTitleForCommand(actionCommand) {
	let current = actionCommand;
	while (current.parent && current.parent.parent) current = current.parent;
	const name = current.name();
	const cliName = resolveCliName();
	if (!name || name === cliName) return;
	process.title = `${cliName}-${name}`;
}
const PLUGIN_REQUIRED_COMMANDS = new Set([
	"message",
	"channels",
	"directory"
]);
function registerPreActionHooks(program, programVersion) {
	program.hook("preAction", async (_thisCommand, actionCommand) => {
		setProcessTitleForCommand(actionCommand);
		const argv = process.argv;
		if (hasHelpOrVersion(argv)) return;
		const commandPath = getCommandPath(argv, 2);
		if (!(isTruthyEnvValue(process.env.OPENCLAW_HIDE_BANNER) || commandPath[0] === "update" || commandPath[0] === "completion" || commandPath[0] === "plugins" && commandPath[1] === "update")) emitCliBanner(programVersion);
		const verbose = getVerboseFlag(argv, { includeDebug: true });
		setVerbose(verbose);
		if (!verbose) process.env.NODE_NO_WARNINGS ??= "1";
		if (commandPath[0] === "doctor" || commandPath[0] === "completion") return;
		await ensureConfigReady({
			runtime: defaultRuntime,
			commandPath
		});
		if (PLUGIN_REQUIRED_COMMANDS.has(commandPath[0])) ensurePluginRegistryLoaded();
	});
}

//#endregion
//#region src/cli/program/build-program.ts
function buildProgram() {
	const program = new Command();
	const ctx = createProgramContext();
	const argv = process.argv;
	configureProgramHelp(program, ctx);
	registerPreActionHooks(program, ctx.programVersion);
	registerProgramCommands(program, ctx, argv);
	return program;
}

//#endregion
export { buildProgram };
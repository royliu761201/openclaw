import { l as resolveAgentWorkspaceDir, r as listAgentIds } from "../../run-with-concurrency-_Xv7jMpx.js";
import "../../paths-hfkBoC7i.js";
import { a as defaultRuntime, t as createSubsystemLogger } from "../../subsystem-DQJPqN9H.js";
import { B as resolveAgentIdFromSessionKey } from "../../workspace-Cez7tM9z.js";
import "../../logger-C6eFjEx8.js";
import "../../model-selection-Dlz_Qmqi.js";
import "../../github-copilot-token-CQmATy5E.js";
import { a as isGatewayStartupEvent } from "../../legacy-names-DeWhx4AY.js";
import "../../thinking-Bhkz_OAl.js";
import { n as SILENT_REPLY_TOKEN } from "../../tokens-CPCWTGYC.js";
import { o as agentCommand, s as createDefaultDeps } from "../../pi-embedded-D9aoNcl8.js";
import "../../plugins-iJTtkY2_.js";
import "../../accounts-DrJKnY0B.js";
import "../../send-CtSdEFh-.js";
import "../../send-0wPrKyxN.js";
import "../../deliver-BxDu_GCF.js";
import "../../diagnostic-BUKLn-_j.js";
import "../../accounts-CE9KWRU2.js";
import "../../image-ops-BwGzrtHo.js";
import "../../send-DufKnq0R.js";
import "../../pi-model-discovery-pYrYVQqE.js";
import { Dt as resolveAgentMainSessionKey, W as loadSessionStore, Y as updateSessionStore, kt as resolveMainSessionKey } from "../../pi-embedded-helpers-nvwNNFVg.js";
import "../../chrome-Cu4MAo8M.js";
import "../../frontmatter-BAic8FWM.js";
import "../../skills-BFWox_AX.js";
import "../../path-alias-guards-457JCSHr.js";
import "../../proxy-env-DKXuS04c.js";
import "../../redact-Coev2L_A.js";
import "../../errors-DbcY9zSC.js";
import "../../fs-safe-CnL2SWY6.js";
import "../../store-DE2mwsSi.js";
import { s as resolveStorePath } from "../../paths-D_dtI_RW.js";
import "../../tool-images-CGZO341K.js";
import "../../image-YPbekh_o.js";
import "../../audio-transcription-runner-ByY-8AXe.js";
import "../../fetch-UqGz2TM1.js";
import "../../fetch-guard-BFt2Tveu.js";
import "../../api-key-rotation-CtVz75QR.js";
import "../../proxy-fetch-DMQEaYIu.js";
import "../../ir-BwkxGUCH.js";
import "../../render-7C7EDC8_.js";
import "../../target-errors-L9sQ9YV2.js";
import "../../commands-registry-KW-ZGuTn.js";
import "../../skill-commands-SCA7gylN.js";
import "../../fetch-CONQGbzL.js";
import "../../channel-activity-YsS3xJh-.js";
import "../../tables-kGiKzDN2.js";
import "../../send-8I9vebLR.js";
import "../../outbound-attachment-BCWRRVJ9.js";
import "../../send-tAuhiitS.js";
import "../../proxy-o7sro0Y0.js";
import "../../manager-DKV9fHfm.js";
import "../../query-expansion-CMYNFEdb.js";
import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
//#region src/gateway/boot.ts
function generateBootSessionId() {
	return `boot-${(/* @__PURE__ */ new Date()).toISOString().replace(/[:.]/g, "-").replace("T", "_").replace("Z", "")}-${crypto.randomUUID().slice(0, 8)}`;
}
const log$1 = createSubsystemLogger("gateway/boot");
const BOOT_FILENAME = "BOOT.md";
function buildBootPrompt(content) {
	return [
		"You are running a boot check. Follow BOOT.md instructions exactly.",
		"",
		"BOOT.md:",
		content,
		"",
		"If BOOT.md asks you to send a message, use the message tool (action=send with channel + target).",
		"Use the `target` field (not `to`) for message tool destinations.",
		`After sending with the message tool, reply with ONLY: ${SILENT_REPLY_TOKEN}.`,
		`If nothing needs attention, reply with ONLY: ${SILENT_REPLY_TOKEN}.`
	].join("\n");
}
async function loadBootFile(workspaceDir) {
	const bootPath = path.join(workspaceDir, BOOT_FILENAME);
	try {
		const trimmed = (await fs.readFile(bootPath, "utf-8")).trim();
		if (!trimmed) return { status: "empty" };
		return {
			status: "ok",
			content: trimmed
		};
	} catch (err) {
		if (err.code === "ENOENT") return { status: "missing" };
		throw err;
	}
}
function snapshotMainSessionMapping(params) {
	const agentId = resolveAgentIdFromSessionKey(params.sessionKey);
	const storePath = resolveStorePath(params.cfg.session?.store, { agentId });
	try {
		const entry = loadSessionStore(storePath, { skipCache: true })[params.sessionKey];
		if (!entry) return {
			storePath,
			sessionKey: params.sessionKey,
			canRestore: true,
			hadEntry: false
		};
		return {
			storePath,
			sessionKey: params.sessionKey,
			canRestore: true,
			hadEntry: true,
			entry: structuredClone(entry)
		};
	} catch (err) {
		log$1.debug("boot: could not snapshot main session mapping", {
			sessionKey: params.sessionKey,
			error: String(err)
		});
		return {
			storePath,
			sessionKey: params.sessionKey,
			canRestore: false,
			hadEntry: false
		};
	}
}
async function restoreMainSessionMapping(snapshot) {
	if (!snapshot.canRestore) return;
	try {
		await updateSessionStore(snapshot.storePath, (store) => {
			if (snapshot.hadEntry && snapshot.entry) {
				store[snapshot.sessionKey] = snapshot.entry;
				return;
			}
			delete store[snapshot.sessionKey];
		}, { activeSessionKey: snapshot.sessionKey });
		return;
	} catch (err) {
		return err instanceof Error ? err.message : String(err);
	}
}
async function runBootOnce(params) {
	const bootRuntime = {
		log: () => {},
		error: (message) => log$1.error(String(message)),
		exit: defaultRuntime.exit
	};
	let result;
	try {
		result = await loadBootFile(params.workspaceDir);
	} catch (err) {
		const message = err instanceof Error ? err.message : String(err);
		log$1.error(`boot: failed to read ${BOOT_FILENAME}: ${message}`);
		return {
			status: "failed",
			reason: message
		};
	}
	if (result.status === "missing" || result.status === "empty") return {
		status: "skipped",
		reason: result.status
	};
	const sessionKey = params.agentId ? resolveAgentMainSessionKey({
		cfg: params.cfg,
		agentId: params.agentId
	}) : resolveMainSessionKey(params.cfg);
	const message = buildBootPrompt(result.content ?? "");
	const sessionId = generateBootSessionId();
	const mappingSnapshot = snapshotMainSessionMapping({
		cfg: params.cfg,
		sessionKey
	});
	let agentFailure;
	try {
		await agentCommand({
			message,
			sessionKey,
			sessionId,
			deliver: false,
			senderIsOwner: true
		}, bootRuntime, params.deps);
	} catch (err) {
		agentFailure = err instanceof Error ? err.message : String(err);
		log$1.error(`boot: agent run failed: ${agentFailure}`);
	}
	const mappingRestoreFailure = await restoreMainSessionMapping(mappingSnapshot);
	if (mappingRestoreFailure) log$1.error(`boot: failed to restore main session mapping: ${mappingRestoreFailure}`);
	if (!agentFailure && !mappingRestoreFailure) return { status: "ran" };
	return {
		status: "failed",
		reason: [agentFailure ? `agent run failed: ${agentFailure}` : void 0, mappingRestoreFailure ? `mapping restore failed: ${mappingRestoreFailure}` : void 0].filter((part) => Boolean(part)).join("; ")
	};
}
//#endregion
//#region src/hooks/bundled/boot-md/handler.ts
const log = createSubsystemLogger("hooks/boot-md");
const runBootChecklist = async (event) => {
	if (!isGatewayStartupEvent(event)) return;
	if (!event.context.cfg) return;
	const cfg = event.context.cfg;
	const deps = event.context.deps ?? createDefaultDeps();
	const agentIds = listAgentIds(cfg);
	for (const agentId of agentIds) {
		const workspaceDir = resolveAgentWorkspaceDir(cfg, agentId);
		const result = await runBootOnce({
			cfg,
			deps,
			workspaceDir,
			agentId
		});
		if (result.status === "failed") {
			log.warn("boot-md failed for agent startup run", {
				agentId,
				workspaceDir,
				reason: result.reason
			});
			continue;
		}
		if (result.status === "skipped") log.debug("boot-md skipped for agent startup run", {
			agentId,
			workspaceDir,
			reason: result.reason
		});
	}
};
//#endregion
export { runBootChecklist as default };

import { a as resolveAgentDir, l as resolveAgentWorkspaceDir, o as resolveAgentEffectiveModelPrimary, u as resolveDefaultAgentId } from "./run-with-concurrency-_Xv7jMpx.js";
import "./paths-hfkBoC7i.js";
import { t as createSubsystemLogger } from "./subsystem-DQJPqN9H.js";
import "./workspace-Cez7tM9z.js";
import "./logger-C6eFjEx8.js";
import { Ar as DEFAULT_PROVIDER, l as parseModelRef } from "./model-selection-Dlz_Qmqi.js";
import "./github-copilot-token-CQmATy5E.js";
import "./legacy-names-DeWhx4AY.js";
import "./thinking-Bhkz_OAl.js";
import "./tokens-CPCWTGYC.js";
import { t as runEmbeddedPiAgent } from "./pi-embedded-D9aoNcl8.js";
import "./plugins-iJTtkY2_.js";
import "./accounts-DrJKnY0B.js";
import "./send-CtSdEFh-.js";
import "./send-0wPrKyxN.js";
import "./deliver-BxDu_GCF.js";
import "./diagnostic-BUKLn-_j.js";
import "./accounts-CE9KWRU2.js";
import "./image-ops-BwGzrtHo.js";
import "./send-DufKnq0R.js";
import "./pi-model-discovery-pYrYVQqE.js";
import "./pi-embedded-helpers-nvwNNFVg.js";
import "./chrome-Cu4MAo8M.js";
import "./frontmatter-BAic8FWM.js";
import "./skills-BFWox_AX.js";
import "./path-alias-guards-457JCSHr.js";
import "./proxy-env-DKXuS04c.js";
import "./redact-Coev2L_A.js";
import "./errors-DbcY9zSC.js";
import "./fs-safe-CnL2SWY6.js";
import "./store-DE2mwsSi.js";
import "./paths-D_dtI_RW.js";
import "./tool-images-CGZO341K.js";
import "./image-YPbekh_o.js";
import "./audio-transcription-runner-ByY-8AXe.js";
import "./fetch-UqGz2TM1.js";
import "./fetch-guard-BFt2Tveu.js";
import "./api-key-rotation-CtVz75QR.js";
import "./proxy-fetch-DMQEaYIu.js";
import "./ir-BwkxGUCH.js";
import "./render-7C7EDC8_.js";
import "./target-errors-L9sQ9YV2.js";
import "./commands-registry-KW-ZGuTn.js";
import "./skill-commands-SCA7gylN.js";
import "./fetch-CONQGbzL.js";
import "./channel-activity-YsS3xJh-.js";
import "./tables-kGiKzDN2.js";
import "./send-8I9vebLR.js";
import "./outbound-attachment-BCWRRVJ9.js";
import "./send-tAuhiitS.js";
import "./proxy-o7sro0Y0.js";
import "./manager-DKV9fHfm.js";
import "./query-expansion-CMYNFEdb.js";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
//#region src/hooks/llm-slug-generator.ts
/**
* LLM-based slug generator for session memory filenames
*/
const log = createSubsystemLogger("llm-slug-generator");
/**
* Generate a short 1-2 word filename slug from session content using LLM
*/
async function generateSlugViaLLM(params) {
	let tempSessionFile = null;
	try {
		const agentId = resolveDefaultAgentId(params.cfg);
		const workspaceDir = resolveAgentWorkspaceDir(params.cfg, agentId);
		const agentDir = resolveAgentDir(params.cfg, agentId);
		const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "openclaw-slug-"));
		tempSessionFile = path.join(tempDir, "session.jsonl");
		const prompt = `Based on this conversation, generate a short 1-2 word filename slug (lowercase, hyphen-separated, no file extension).

Conversation summary:
${params.sessionContent.slice(0, 2e3)}

Reply with ONLY the slug, nothing else. Examples: "vendor-pitch", "api-design", "bug-fix"`;
		const modelRef = resolveAgentEffectiveModelPrimary(params.cfg, agentId);
		const parsed = modelRef ? parseModelRef(modelRef, DEFAULT_PROVIDER) : null;
		const provider = parsed?.provider ?? "anthropic";
		const model = parsed?.model ?? "claude-opus-4-6";
		const result = await runEmbeddedPiAgent({
			sessionId: `slug-generator-${Date.now()}`,
			sessionKey: "temp:slug-generator",
			agentId,
			sessionFile: tempSessionFile,
			workspaceDir,
			agentDir,
			config: params.cfg,
			prompt,
			provider,
			model,
			timeoutMs: 15e3,
			runId: `slug-gen-${Date.now()}`
		});
		if (result.payloads && result.payloads.length > 0) {
			const text = result.payloads[0]?.text;
			if (text) return text.trim().toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "").slice(0, 30) || null;
		}
		return null;
	} catch (err) {
		const message = err instanceof Error ? err.stack ?? err.message : String(err);
		log.error(`Failed to generate slug: ${message}`);
		return null;
	} finally {
		if (tempSessionFile) try {
			await fs.rm(path.dirname(tempSessionFile), {
				recursive: true,
				force: true
			});
		} catch {}
	}
}
//#endregion
export { generateSlugViaLLM };

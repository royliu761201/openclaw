import "./paths-DVBShlw6.js";
import { A as logVerbose, N as shouldLogVerbose } from "./subsystem-DHfJG4gk.js";
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
import { a as runCapability, l as isAudioAttachment, n as createMediaAttachmentCache, r as normalizeMediaAttachments, t as buildProviderRegistry } from "./runner-DNThkTtX.js";
import "./image-BFquFRGY.js";
import "./pi-model-discovery-EwKVHlZB.js";
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
import "./fetch-TYcqD9fC.js";

//#region src/media-understanding/audio-preflight.ts
/**
* Transcribes the first audio attachment BEFORE mention checking.
* This allows voice notes to be processed in group chats with requireMention: true.
* Returns the transcript or undefined if transcription fails or no audio is found.
*/
async function transcribeFirstAudio(params) {
	const { ctx, cfg } = params;
	const audioConfig = cfg.tools?.media?.audio;
	if (!audioConfig || audioConfig.enabled === false) return;
	const attachments = normalizeMediaAttachments(ctx);
	if (!attachments || attachments.length === 0) return;
	const firstAudio = attachments.find((att) => att && isAudioAttachment(att) && !att.alreadyTranscribed);
	if (!firstAudio) return;
	if (shouldLogVerbose()) logVerbose(`audio-preflight: transcribing attachment ${firstAudio.index} for mention check`);
	const providerRegistry = buildProviderRegistry(params.providers);
	const cache = createMediaAttachmentCache(attachments);
	try {
		const result = await runCapability({
			capability: "audio",
			cfg,
			ctx,
			attachments: cache,
			media: attachments,
			agentDir: params.agentDir,
			providerRegistry,
			config: audioConfig,
			activeModel: params.activeModel
		});
		if (!result || result.outputs.length === 0) return;
		const audioOutput = result.outputs.find((output) => output.kind === "audio.transcription");
		if (!audioOutput || !audioOutput.text) return;
		firstAudio.alreadyTranscribed = true;
		if (shouldLogVerbose()) logVerbose(`audio-preflight: transcribed ${audioOutput.text.length} chars from attachment ${firstAudio.index}`);
		return audioOutput.text;
	} catch (err) {
		if (shouldLogVerbose()) logVerbose(`audio-preflight: transcription failed: ${String(err)}`);
		return;
	} finally {
		await cache.cleanup();
	}
}

//#endregion
export { transcribeFirstAudio };
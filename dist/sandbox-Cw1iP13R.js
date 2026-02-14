import { r as STATE_DIR } from "./paths-DVBShlw6.js";
import { c as defaultRuntime, m as CHAT_CHANNEL_ORDER, p as CHANNEL_IDS, t as createSubsystemLogger, v as getChatChannelMeta, w as requireActivePluginRegistry } from "./subsystem-DHfJG4gk.js";
import { b as resolveUserPath, h as normalizeE164, l as escapeRegExp } from "./utils-BtIMES3N.js";
import { c as normalizeAccountId$1, d as resolveAgentIdFromSessionKey, i as buildAgentMainSessionKey, l as normalizeAgentId, n as DEFAULT_AGENT_ID, t as DEFAULT_ACCOUNT_ID, u as normalizeMainKey } from "./session-key-BWxPj0z_.js";
import { b as DEFAULT_USER_FILENAME, d as DEFAULT_AGENTS_FILENAME, f as DEFAULT_AGENT_WORKSPACE_DIR, h as DEFAULT_IDENTITY_FILENAME, l as resolveSessionAgentId, m as DEFAULT_HEARTBEAT_FILENAME, n as resolveAgentConfig, p as DEFAULT_BOOTSTRAP_FILENAME, v as DEFAULT_SOUL_FILENAME, x as ensureAgentWorkspace, y as DEFAULT_TOOLS_FILENAME } from "./agent-scope-D_p2LOiK.js";
import { t as formatCliCommand } from "./command-format-ChfKqObn.js";
import { d as parseByteSize, g as parseDurationMs, i as loadConfig } from "./config-C4SM4a2M.js";
import { a as normalizeWhatsAppTarget, b as normalizeChatType, c as resolveTelegramAccount, m as resolveSlackReplyToMode, p as resolveSlackAccount, r as normalizeChannelId, v as resolveDiscordAccount } from "./plugins-BvNdouUY.js";
import { A as DEFAULT_BROWSER_EVALUATE_ENABLED, N as DEFAULT_OPENCLAW_BROWSER_PROFILE_NAME, j as DEFAULT_OPENCLAW_BROWSER_COLOR } from "./chrome-BtcIWBGj.js";
import { d as resolveSandboxPath, o as syncSkillsToWorkspace } from "./skills-Dz15dAM4.js";
import { t as registerBrowserRoutes } from "./routes-BF4kTHtn.js";
import { a as resolveProfile, t as createBrowserRouteContext } from "./server-context-B5b9OM_w.js";
import { c as listDeliverableMessageChannels, l as normalizeMessageChannel } from "./message-channel-CTtrEkmW.js";
import { n as resolveWhatsAppAccount } from "./accounts-54zZMYCo.js";
import { n as resolveSessionFilePath, t as resolveDefaultSessionStorePath } from "./paths-DdKf4lHp.js";
import { t as emitSessionTranscriptUpdate } from "./transcript-events-Bp7fGnwv.js";
import fs from "node:fs";
import path from "node:path";
import fs$1 from "node:fs/promises";
import { spawn } from "node:child_process";
import crypto from "node:crypto";
import { CURRENT_SESSION_VERSION, SessionManager } from "@mariozechner/pi-coding-agent";
import express from "express";

//#region src/channels/conversation-label.ts
function extractConversationId(from) {
	const trimmed = from?.trim();
	if (!trimmed) return;
	const parts = trimmed.split(":").filter(Boolean);
	return parts.length > 0 ? parts[parts.length - 1] : trimmed;
}
function shouldAppendId(id) {
	if (/^[0-9]+$/.test(id)) return true;
	if (id.includes("@g.us")) return true;
	return false;
}
function resolveConversationLabel(ctx) {
	const explicit = ctx.ConversationLabel?.trim();
	if (explicit) return explicit;
	const threadLabel = ctx.ThreadLabel?.trim();
	if (threadLabel) return threadLabel;
	if (normalizeChatType(ctx.ChatType) === "direct") return ctx.SenderName?.trim() || ctx.From?.trim() || void 0;
	const base = ctx.GroupChannel?.trim() || ctx.GroupSubject?.trim() || ctx.GroupSpace?.trim() || ctx.From?.trim() || "";
	if (!base) return;
	const id = extractConversationId(ctx.From);
	if (!id) return base;
	if (!shouldAppendId(id)) return base;
	if (base === id) return base;
	if (base.includes(id)) return base;
	if (base.toLowerCase().includes(" id:")) return base;
	if (base.startsWith("#") || base.startsWith("@")) return base;
	return `${base} id:${id}`;
}

//#endregion
//#region src/agents/sandbox/constants.ts
const DEFAULT_SANDBOX_WORKSPACE_ROOT = path.join(STATE_DIR, "sandboxes");
const DEFAULT_SANDBOX_IMAGE = "openclaw-sandbox:bookworm-slim";
const DEFAULT_SANDBOX_CONTAINER_PREFIX = "openclaw-sbx-";
const DEFAULT_SANDBOX_WORKDIR = "/workspace";
const DEFAULT_SANDBOX_IDLE_HOURS = 24;
const DEFAULT_SANDBOX_MAX_AGE_DAYS = 7;
const DEFAULT_TOOL_ALLOW = [
	"exec",
	"process",
	"read",
	"write",
	"edit",
	"apply_patch",
	"image",
	"sessions_list",
	"sessions_history",
	"sessions_send",
	"sessions_spawn",
	"session_status"
];
const DEFAULT_TOOL_DENY = [
	"browser",
	"canvas",
	"nodes",
	"cron",
	"gateway",
	...CHANNEL_IDS
];
const DEFAULT_SANDBOX_BROWSER_IMAGE = "openclaw-sandbox-browser:bookworm-slim";
const DEFAULT_SANDBOX_COMMON_IMAGE = "openclaw-sandbox-common:bookworm-slim";
const DEFAULT_SANDBOX_BROWSER_PREFIX = "openclaw-sbx-browser-";
const DEFAULT_SANDBOX_BROWSER_CDP_PORT = 9222;
const DEFAULT_SANDBOX_BROWSER_VNC_PORT = 5900;
const DEFAULT_SANDBOX_BROWSER_NOVNC_PORT = 6080;
const DEFAULT_SANDBOX_BROWSER_AUTOSTART_TIMEOUT_MS = 12e3;
const SANDBOX_AGENT_WORKSPACE_MOUNT = "/agent";
const SANDBOX_STATE_DIR = path.join(STATE_DIR, "sandbox");
const SANDBOX_REGISTRY_PATH = path.join(SANDBOX_STATE_DIR, "containers.json");
const SANDBOX_BROWSER_REGISTRY_PATH = path.join(SANDBOX_STATE_DIR, "browsers.json");

//#endregion
//#region src/agents/tool-policy.ts
const TOOL_NAME_ALIASES = {
	bash: "exec",
	"apply-patch": "apply_patch"
};
const TOOL_GROUPS = {
	"group:memory": ["memory_search", "memory_get"],
	"group:web": ["web_search", "web_fetch"],
	"group:fs": [
		"read",
		"write",
		"edit",
		"apply_patch"
	],
	"group:runtime": ["exec", "process"],
	"group:sessions": [
		"sessions_list",
		"sessions_history",
		"sessions_send",
		"sessions_spawn",
		"session_status"
	],
	"group:ui": ["browser", "canvas"],
	"group:automation": ["cron", "gateway"],
	"group:messaging": ["message"],
	"group:nodes": ["nodes"],
	"group:openclaw": [
		"browser",
		"canvas",
		"nodes",
		"cron",
		"message",
		"gateway",
		"agents_list",
		"sessions_list",
		"sessions_history",
		"sessions_send",
		"sessions_spawn",
		"session_status",
		"memory_search",
		"memory_get",
		"web_search",
		"web_fetch",
		"image"
	]
};
const OWNER_ONLY_TOOL_NAMES = new Set(["whatsapp_login"]);
const TOOL_PROFILES = {
	minimal: { allow: ["session_status"] },
	coding: { allow: [
		"group:fs",
		"group:runtime",
		"group:sessions",
		"group:memory",
		"image"
	] },
	messaging: { allow: [
		"group:messaging",
		"sessions_list",
		"sessions_history",
		"sessions_send",
		"session_status"
	] },
	full: {}
};
function normalizeToolName(name) {
	const normalized = name.trim().toLowerCase();
	return TOOL_NAME_ALIASES[normalized] ?? normalized;
}
function isOwnerOnlyToolName(name) {
	return OWNER_ONLY_TOOL_NAMES.has(normalizeToolName(name));
}
function applyOwnerOnlyToolPolicy(tools, senderIsOwner) {
	const withGuard = tools.map((tool) => {
		if (!isOwnerOnlyToolName(tool.name)) return tool;
		if (senderIsOwner || !tool.execute) return tool;
		return {
			...tool,
			execute: async () => {
				throw new Error("Tool restricted to owner senders.");
			}
		};
	});
	if (senderIsOwner) return withGuard;
	return withGuard.filter((tool) => !isOwnerOnlyToolName(tool.name));
}
function normalizeToolList(list) {
	if (!list) return [];
	return list.map(normalizeToolName).filter(Boolean);
}
function expandToolGroups(list) {
	const normalized = normalizeToolList(list);
	const expanded = [];
	for (const value of normalized) {
		const group = TOOL_GROUPS[value];
		if (group) {
			expanded.push(...group);
			continue;
		}
		expanded.push(value);
	}
	return Array.from(new Set(expanded));
}
function collectExplicitAllowlist(policies) {
	const entries = [];
	for (const policy of policies) {
		if (!policy?.allow) continue;
		for (const value of policy.allow) {
			if (typeof value !== "string") continue;
			const trimmed = value.trim();
			if (trimmed) entries.push(trimmed);
		}
	}
	return entries;
}
function buildPluginToolGroups(params) {
	const all = [];
	const byPlugin = /* @__PURE__ */ new Map();
	for (const tool of params.tools) {
		const meta = params.toolMeta(tool);
		if (!meta) continue;
		const name = normalizeToolName(tool.name);
		all.push(name);
		const pluginId = meta.pluginId.toLowerCase();
		const list = byPlugin.get(pluginId) ?? [];
		list.push(name);
		byPlugin.set(pluginId, list);
	}
	return {
		all,
		byPlugin
	};
}
function expandPluginGroups(list, groups) {
	if (!list || list.length === 0) return list;
	const expanded = [];
	for (const entry of list) {
		const normalized = normalizeToolName(entry);
		if (normalized === "group:plugins") {
			if (groups.all.length > 0) expanded.push(...groups.all);
			else expanded.push(normalized);
			continue;
		}
		const tools = groups.byPlugin.get(normalized);
		if (tools && tools.length > 0) {
			expanded.push(...tools);
			continue;
		}
		expanded.push(normalized);
	}
	return Array.from(new Set(expanded));
}
function expandPolicyWithPluginGroups(policy, groups) {
	if (!policy) return;
	return {
		allow: expandPluginGroups(policy.allow, groups),
		deny: expandPluginGroups(policy.deny, groups)
	};
}
function stripPluginOnlyAllowlist(policy, groups, coreTools) {
	if (!policy?.allow || policy.allow.length === 0) return {
		policy,
		unknownAllowlist: [],
		strippedAllowlist: false
	};
	const normalized = normalizeToolList(policy.allow);
	if (normalized.length === 0) return {
		policy,
		unknownAllowlist: [],
		strippedAllowlist: false
	};
	const pluginIds = new Set(groups.byPlugin.keys());
	const pluginTools = new Set(groups.all);
	const unknownAllowlist = [];
	let hasCoreEntry = false;
	for (const entry of normalized) {
		if (entry === "*") {
			hasCoreEntry = true;
			continue;
		}
		const isPluginEntry = entry === "group:plugins" || pluginIds.has(entry) || pluginTools.has(entry);
		const isCoreEntry = expandToolGroups([entry]).some((tool) => coreTools.has(tool));
		if (isCoreEntry) hasCoreEntry = true;
		if (!isCoreEntry && !isPluginEntry) unknownAllowlist.push(entry);
	}
	const strippedAllowlist = !hasCoreEntry;
	if (strippedAllowlist) {}
	return {
		policy: strippedAllowlist ? {
			...policy,
			allow: void 0
		} : policy,
		unknownAllowlist: Array.from(new Set(unknownAllowlist)),
		strippedAllowlist
	};
}
function resolveToolProfilePolicy(profile) {
	if (!profile) return;
	const resolved = TOOL_PROFILES[profile];
	if (!resolved) return;
	if (!resolved.allow && !resolved.deny) return;
	return {
		allow: resolved.allow ? [...resolved.allow] : void 0,
		deny: resolved.deny ? [...resolved.deny] : void 0
	};
}

//#endregion
//#region src/agents/sandbox/tool-policy.ts
function compilePattern(pattern) {
	const normalized = pattern.trim().toLowerCase();
	if (!normalized) return {
		kind: "exact",
		value: ""
	};
	if (normalized === "*") return { kind: "all" };
	if (!normalized.includes("*")) return {
		kind: "exact",
		value: normalized
	};
	const escaped = normalized.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	return {
		kind: "regex",
		value: new RegExp(`^${escaped.replaceAll("\\*", ".*")}$`)
	};
}
function compilePatterns(patterns) {
	if (!Array.isArray(patterns)) return [];
	return expandToolGroups(patterns).map(compilePattern).filter((pattern) => pattern.kind !== "exact" || pattern.value);
}
function matchesAny(name, patterns) {
	for (const pattern of patterns) {
		if (pattern.kind === "all") return true;
		if (pattern.kind === "exact" && name === pattern.value) return true;
		if (pattern.kind === "regex" && pattern.value.test(name)) return true;
	}
	return false;
}
function isToolAllowed(policy, name) {
	const normalized = name.trim().toLowerCase();
	if (matchesAny(normalized, compilePatterns(policy.deny))) return false;
	const allow = compilePatterns(policy.allow);
	if (allow.length === 0) return true;
	return matchesAny(normalized, allow);
}
function resolveSandboxToolPolicyForAgent(cfg, agentId) {
	const agentConfig = cfg && agentId ? resolveAgentConfig(cfg, agentId) : void 0;
	const agentAllow = agentConfig?.tools?.sandbox?.tools?.allow;
	const agentDeny = agentConfig?.tools?.sandbox?.tools?.deny;
	const globalAllow = cfg?.tools?.sandbox?.tools?.allow;
	const globalDeny = cfg?.tools?.sandbox?.tools?.deny;
	const allowSource = Array.isArray(agentAllow) ? {
		source: "agent",
		key: "agents.list[].tools.sandbox.tools.allow"
	} : Array.isArray(globalAllow) ? {
		source: "global",
		key: "tools.sandbox.tools.allow"
	} : {
		source: "default",
		key: "tools.sandbox.tools.allow"
	};
	const denySource = Array.isArray(agentDeny) ? {
		source: "agent",
		key: "agents.list[].tools.sandbox.tools.deny"
	} : Array.isArray(globalDeny) ? {
		source: "global",
		key: "tools.sandbox.tools.deny"
	} : {
		source: "default",
		key: "tools.sandbox.tools.deny"
	};
	const deny = Array.isArray(agentDeny) ? agentDeny : Array.isArray(globalDeny) ? globalDeny : [...DEFAULT_TOOL_DENY];
	const allow = Array.isArray(agentAllow) ? agentAllow : Array.isArray(globalAllow) ? globalAllow : [...DEFAULT_TOOL_ALLOW];
	const expandedDeny = expandToolGroups(deny);
	let expandedAllow = expandToolGroups(allow);
	if (!expandedDeny.map((v) => v.toLowerCase()).includes("image") && !expandedAllow.map((v) => v.toLowerCase()).includes("image")) expandedAllow = [...expandedAllow, "image"];
	return {
		allow: expandedAllow,
		deny: expandedDeny,
		sources: {
			allow: allowSource,
			deny: denySource
		}
	};
}

//#endregion
//#region src/agents/sandbox/config.ts
function resolveSandboxScope(params) {
	if (params.scope) return params.scope;
	if (typeof params.perSession === "boolean") return params.perSession ? "session" : "shared";
	return "agent";
}
function resolveSandboxDockerConfig(params) {
	const agentDocker = params.scope === "shared" ? void 0 : params.agentDocker;
	const globalDocker = params.globalDocker;
	const env = agentDocker?.env ? {
		...globalDocker?.env ?? { LANG: "C.UTF-8" },
		...agentDocker.env
	} : globalDocker?.env ?? { LANG: "C.UTF-8" };
	const ulimits = agentDocker?.ulimits ? {
		...globalDocker?.ulimits,
		...agentDocker.ulimits
	} : globalDocker?.ulimits;
	const binds = [...globalDocker?.binds ?? [], ...agentDocker?.binds ?? []];
	return {
		image: agentDocker?.image ?? globalDocker?.image ?? DEFAULT_SANDBOX_IMAGE,
		containerPrefix: agentDocker?.containerPrefix ?? globalDocker?.containerPrefix ?? DEFAULT_SANDBOX_CONTAINER_PREFIX,
		workdir: agentDocker?.workdir ?? globalDocker?.workdir ?? DEFAULT_SANDBOX_WORKDIR,
		readOnlyRoot: agentDocker?.readOnlyRoot ?? globalDocker?.readOnlyRoot ?? true,
		tmpfs: agentDocker?.tmpfs ?? globalDocker?.tmpfs ?? [
			"/tmp",
			"/var/tmp",
			"/run"
		],
		network: agentDocker?.network ?? globalDocker?.network ?? "none",
		user: agentDocker?.user ?? globalDocker?.user,
		capDrop: agentDocker?.capDrop ?? globalDocker?.capDrop ?? ["ALL"],
		env,
		setupCommand: agentDocker?.setupCommand ?? globalDocker?.setupCommand,
		pidsLimit: agentDocker?.pidsLimit ?? globalDocker?.pidsLimit,
		memory: agentDocker?.memory ?? globalDocker?.memory,
		memorySwap: agentDocker?.memorySwap ?? globalDocker?.memorySwap,
		cpus: agentDocker?.cpus ?? globalDocker?.cpus,
		ulimits,
		seccompProfile: agentDocker?.seccompProfile ?? globalDocker?.seccompProfile,
		apparmorProfile: agentDocker?.apparmorProfile ?? globalDocker?.apparmorProfile,
		dns: agentDocker?.dns ?? globalDocker?.dns,
		extraHosts: agentDocker?.extraHosts ?? globalDocker?.extraHosts,
		binds: binds.length ? binds : void 0
	};
}
function resolveSandboxBrowserConfig(params) {
	const agentBrowser = params.scope === "shared" ? void 0 : params.agentBrowser;
	const globalBrowser = params.globalBrowser;
	return {
		enabled: agentBrowser?.enabled ?? globalBrowser?.enabled ?? false,
		image: agentBrowser?.image ?? globalBrowser?.image ?? DEFAULT_SANDBOX_BROWSER_IMAGE,
		containerPrefix: agentBrowser?.containerPrefix ?? globalBrowser?.containerPrefix ?? DEFAULT_SANDBOX_BROWSER_PREFIX,
		cdpPort: agentBrowser?.cdpPort ?? globalBrowser?.cdpPort ?? DEFAULT_SANDBOX_BROWSER_CDP_PORT,
		vncPort: agentBrowser?.vncPort ?? globalBrowser?.vncPort ?? DEFAULT_SANDBOX_BROWSER_VNC_PORT,
		noVncPort: agentBrowser?.noVncPort ?? globalBrowser?.noVncPort ?? DEFAULT_SANDBOX_BROWSER_NOVNC_PORT,
		headless: agentBrowser?.headless ?? globalBrowser?.headless ?? false,
		enableNoVnc: agentBrowser?.enableNoVnc ?? globalBrowser?.enableNoVnc ?? true,
		allowHostControl: agentBrowser?.allowHostControl ?? globalBrowser?.allowHostControl ?? false,
		autoStart: agentBrowser?.autoStart ?? globalBrowser?.autoStart ?? true,
		autoStartTimeoutMs: agentBrowser?.autoStartTimeoutMs ?? globalBrowser?.autoStartTimeoutMs ?? DEFAULT_SANDBOX_BROWSER_AUTOSTART_TIMEOUT_MS
	};
}
function resolveSandboxPruneConfig(params) {
	const agentPrune = params.scope === "shared" ? void 0 : params.agentPrune;
	const globalPrune = params.globalPrune;
	return {
		idleHours: agentPrune?.idleHours ?? globalPrune?.idleHours ?? DEFAULT_SANDBOX_IDLE_HOURS,
		maxAgeDays: agentPrune?.maxAgeDays ?? globalPrune?.maxAgeDays ?? DEFAULT_SANDBOX_MAX_AGE_DAYS
	};
}
function resolveSandboxConfigForAgent(cfg, agentId) {
	const agent = cfg?.agents?.defaults?.sandbox;
	let agentSandbox;
	const agentConfig = cfg && agentId ? resolveAgentConfig(cfg, agentId) : void 0;
	if (agentConfig?.sandbox) agentSandbox = agentConfig.sandbox;
	const scope = resolveSandboxScope({
		scope: agentSandbox?.scope ?? agent?.scope,
		perSession: agentSandbox?.perSession ?? agent?.perSession
	});
	const toolPolicy = resolveSandboxToolPolicyForAgent(cfg, agentId);
	return {
		mode: agentSandbox?.mode ?? agent?.mode ?? "off",
		scope,
		workspaceAccess: agentSandbox?.workspaceAccess ?? agent?.workspaceAccess ?? "none",
		workspaceRoot: agentSandbox?.workspaceRoot ?? agent?.workspaceRoot ?? DEFAULT_SANDBOX_WORKSPACE_ROOT,
		docker: resolveSandboxDockerConfig({
			scope,
			globalDocker: agent?.docker,
			agentDocker: agentSandbox?.docker
		}),
		browser: resolveSandboxBrowserConfig({
			scope,
			globalBrowser: agent?.browser,
			agentBrowser: agentSandbox?.browser
		}),
		tools: {
			allow: toolPolicy.allow,
			deny: toolPolicy.deny
		},
		prune: resolveSandboxPruneConfig({
			scope,
			globalPrune: agent?.prune,
			agentPrune: agentSandbox?.prune
		})
	};
}

//#endregion
//#region src/browser/bridge-server.ts
async function startBrowserBridgeServer(params) {
	const host = params.host ?? "127.0.0.1";
	const port = params.port ?? 0;
	const app = express();
	app.use((req, res, next) => {
		const ctrl = new AbortController();
		const abort = () => ctrl.abort(/* @__PURE__ */ new Error("request aborted"));
		req.once("aborted", abort);
		res.once("close", () => {
			if (!res.writableEnded) abort();
		});
		req.signal = ctrl.signal;
		next();
	});
	app.use(express.json({ limit: "1mb" }));
	const authToken = params.authToken?.trim();
	if (authToken) app.use((req, res, next) => {
		if (String(req.headers.authorization ?? "").trim() === `Bearer ${authToken}`) return next();
		res.status(401).send("Unauthorized");
	});
	const state = {
		server: null,
		port,
		resolved: params.resolved,
		profiles: /* @__PURE__ */ new Map()
	};
	registerBrowserRoutes(app, createBrowserRouteContext({
		getState: () => state,
		onEnsureAttachTarget: params.onEnsureAttachTarget
	}));
	const server = await new Promise((resolve, reject) => {
		const s = app.listen(port, host, () => resolve(s));
		s.once("error", reject);
	});
	const resolvedPort = server.address()?.port ?? port;
	state.server = server;
	state.port = resolvedPort;
	state.resolved.controlPort = resolvedPort;
	return {
		server,
		port: resolvedPort,
		baseUrl: `http://${host}:${resolvedPort}`,
		state
	};
}
async function stopBrowserBridgeServer(server) {
	await new Promise((resolve) => {
		server.close(() => resolve());
	});
}

//#endregion
//#region src/agents/sandbox/browser-bridges.ts
const BROWSER_BRIDGES = /* @__PURE__ */ new Map();

//#endregion
//#region src/agents/sandbox/config-hash.ts
function isPrimitive(value) {
	return value === null || typeof value !== "object" && typeof value !== "function";
}
function normalizeForHash(value) {
	if (value === void 0) return;
	if (Array.isArray(value)) {
		const normalized = value.map(normalizeForHash).filter((item) => item !== void 0);
		const primitives = normalized.filter(isPrimitive);
		if (primitives.length === normalized.length) return [...primitives].toSorted((a, b) => primitiveToString(a).localeCompare(primitiveToString(b)));
		return normalized;
	}
	if (value && typeof value === "object") {
		const entries = Object.entries(value).toSorted(([a], [b]) => a.localeCompare(b));
		const normalized = {};
		for (const [key, entryValue] of entries) {
			const next = normalizeForHash(entryValue);
			if (next !== void 0) normalized[key] = next;
		}
		return normalized;
	}
	return value;
}
function primitiveToString(value) {
	if (value === null) return "null";
	if (typeof value === "string") return value;
	if (typeof value === "number") return String(value);
	if (typeof value === "boolean") return value ? "true" : "false";
	return JSON.stringify(value);
}
function computeSandboxConfigHash(input) {
	const payload = normalizeForHash(input);
	const raw = JSON.stringify(payload);
	return crypto.createHash("sha1").update(raw).digest("hex");
}

//#endregion
//#region src/agents/sandbox/registry.ts
async function readRegistry() {
	try {
		const raw = await fs$1.readFile(SANDBOX_REGISTRY_PATH, "utf-8");
		const parsed = JSON.parse(raw);
		if (parsed && Array.isArray(parsed.entries)) return parsed;
	} catch {}
	return { entries: [] };
}
async function writeRegistry(registry) {
	await fs$1.mkdir(SANDBOX_STATE_DIR, { recursive: true });
	await fs$1.writeFile(SANDBOX_REGISTRY_PATH, `${JSON.stringify(registry, null, 2)}\n`, "utf-8");
}
async function updateRegistry(entry) {
	const registry = await readRegistry();
	const existing = registry.entries.find((item) => item.containerName === entry.containerName);
	const next = registry.entries.filter((item) => item.containerName !== entry.containerName);
	next.push({
		...entry,
		createdAtMs: existing?.createdAtMs ?? entry.createdAtMs,
		image: existing?.image ?? entry.image,
		configHash: entry.configHash ?? existing?.configHash
	});
	await writeRegistry({ entries: next });
}
async function removeRegistryEntry(containerName) {
	const registry = await readRegistry();
	const next = registry.entries.filter((item) => item.containerName !== containerName);
	if (next.length === registry.entries.length) return;
	await writeRegistry({ entries: next });
}
async function readBrowserRegistry() {
	try {
		const raw = await fs$1.readFile(SANDBOX_BROWSER_REGISTRY_PATH, "utf-8");
		const parsed = JSON.parse(raw);
		if (parsed && Array.isArray(parsed.entries)) return parsed;
	} catch {}
	return { entries: [] };
}
async function writeBrowserRegistry(registry) {
	await fs$1.mkdir(SANDBOX_STATE_DIR, { recursive: true });
	await fs$1.writeFile(SANDBOX_BROWSER_REGISTRY_PATH, `${JSON.stringify(registry, null, 2)}\n`, "utf-8");
}
async function updateBrowserRegistry(entry) {
	const registry = await readBrowserRegistry();
	const existing = registry.entries.find((item) => item.containerName === entry.containerName);
	const next = registry.entries.filter((item) => item.containerName !== entry.containerName);
	next.push({
		...entry,
		createdAtMs: existing?.createdAtMs ?? entry.createdAtMs,
		image: existing?.image ?? entry.image
	});
	await writeBrowserRegistry({ entries: next });
}
async function removeBrowserRegistryEntry(containerName) {
	const registry = await readBrowserRegistry();
	const next = registry.entries.filter((item) => item.containerName !== containerName);
	if (next.length === registry.entries.length) return;
	await writeBrowserRegistry({ entries: next });
}

//#endregion
//#region src/agents/sandbox/shared.ts
function slugifySessionKey(value) {
	const trimmed = value.trim() || "session";
	const hash = crypto.createHash("sha1").update(trimmed).digest("hex").slice(0, 8);
	return `${trimmed.toLowerCase().replace(/[^a-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 32) || "session"}-${hash}`;
}
function resolveSandboxWorkspaceDir(root, sessionKey) {
	const resolvedRoot = resolveUserPath(root);
	const slug = slugifySessionKey(sessionKey);
	return path.join(resolvedRoot, slug);
}
function resolveSandboxScopeKey(scope, sessionKey) {
	const trimmed = sessionKey.trim() || "main";
	if (scope === "shared") return "shared";
	if (scope === "session") return trimmed;
	return `agent:${resolveAgentIdFromSessionKey(trimmed)}`;
}
function resolveSandboxAgentId(scopeKey) {
	const trimmed = scopeKey.trim();
	if (!trimmed || trimmed === "shared") return;
	const parts = trimmed.split(":").filter(Boolean);
	if (parts[0] === "agent" && parts[1]) return normalizeAgentId(parts[1]);
	return resolveAgentIdFromSessionKey(trimmed);
}

//#endregion
//#region src/agents/sandbox/docker.ts
function createAbortError() {
	const err = /* @__PURE__ */ new Error("Aborted");
	err.name = "AbortError";
	return err;
}
function execDockerRaw(args, opts) {
	return new Promise((resolve, reject) => {
		const child = spawn("docker", args, { stdio: [
			"pipe",
			"pipe",
			"pipe"
		] });
		const stdoutChunks = [];
		const stderrChunks = [];
		let aborted = false;
		const signal = opts?.signal;
		const handleAbort = () => {
			if (aborted) return;
			aborted = true;
			child.kill("SIGTERM");
		};
		if (signal) if (signal.aborted) handleAbort();
		else signal.addEventListener("abort", handleAbort);
		child.stdout?.on("data", (chunk) => {
			stdoutChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
		});
		child.stderr?.on("data", (chunk) => {
			stderrChunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
		});
		child.on("error", (error) => {
			if (signal) signal.removeEventListener("abort", handleAbort);
			reject(error);
		});
		child.on("close", (code) => {
			if (signal) signal.removeEventListener("abort", handleAbort);
			const stdout = Buffer.concat(stdoutChunks);
			const stderr = Buffer.concat(stderrChunks);
			if (aborted || signal?.aborted) {
				reject(createAbortError());
				return;
			}
			const exitCode = code ?? 0;
			if (exitCode !== 0 && !opts?.allowFailure) {
				const message = stderr.length > 0 ? stderr.toString("utf8").trim() : "";
				reject(Object.assign(new Error(message || `docker ${args.join(" ")} failed`), {
					code: exitCode,
					stdout,
					stderr
				}));
				return;
			}
			resolve({
				stdout,
				stderr,
				code: exitCode
			});
		});
		const stdin = child.stdin;
		if (stdin) if (opts?.input !== void 0) stdin.end(opts.input);
		else stdin.end();
	});
}
const HOT_CONTAINER_WINDOW_MS = 300 * 1e3;
async function execDocker(args, opts) {
	const result = await execDockerRaw(args, opts);
	return {
		stdout: result.stdout.toString("utf8"),
		stderr: result.stderr.toString("utf8"),
		code: result.code
	};
}
async function readDockerPort(containerName, port) {
	const result = await execDocker([
		"port",
		containerName,
		`${port}/tcp`
	], { allowFailure: true });
	if (result.code !== 0) return null;
	const match = (result.stdout.trim().split(/\r?\n/)[0] ?? "").match(/:(\d+)\s*$/);
	if (!match) return null;
	const mapped = Number.parseInt(match[1] ?? "", 10);
	return Number.isFinite(mapped) ? mapped : null;
}
async function dockerImageExists(image) {
	const result = await execDocker([
		"image",
		"inspect",
		image
	], { allowFailure: true });
	if (result.code === 0) return true;
	const stderr = result.stderr.trim();
	if (stderr.includes("No such image")) return false;
	throw new Error(`Failed to inspect sandbox image: ${stderr}`);
}
async function ensureDockerImage(image) {
	if (await dockerImageExists(image)) return;
	if (image === DEFAULT_SANDBOX_IMAGE) {
		await execDocker(["pull", "debian:bookworm-slim"]);
		await execDocker([
			"tag",
			"debian:bookworm-slim",
			DEFAULT_SANDBOX_IMAGE
		]);
		return;
	}
	throw new Error(`Sandbox image not found: ${image}. Build or pull it first.`);
}
async function dockerContainerState(name) {
	const result = await execDocker([
		"inspect",
		"-f",
		"{{.State.Running}}",
		name
	], { allowFailure: true });
	if (result.code !== 0) return {
		exists: false,
		running: false
	};
	return {
		exists: true,
		running: result.stdout.trim() === "true"
	};
}
function normalizeDockerLimit(value) {
	if (value === void 0 || value === null) return;
	if (typeof value === "number") return Number.isFinite(value) ? String(value) : void 0;
	const trimmed = value.trim();
	return trimmed ? trimmed : void 0;
}
function formatUlimitValue(name, value) {
	if (!name.trim()) return null;
	if (typeof value === "number" || typeof value === "string") {
		const raw = String(value).trim();
		return raw ? `${name}=${raw}` : null;
	}
	const soft = typeof value.soft === "number" ? Math.max(0, value.soft) : void 0;
	const hard = typeof value.hard === "number" ? Math.max(0, value.hard) : void 0;
	if (soft === void 0 && hard === void 0) return null;
	if (soft === void 0) return `${name}=${hard}`;
	if (hard === void 0) return `${name}=${soft}`;
	return `${name}=${soft}:${hard}`;
}
function buildSandboxCreateArgs(params) {
	const createdAtMs = params.createdAtMs ?? Date.now();
	const args = [
		"create",
		"--name",
		params.name
	];
	args.push("--label", "openclaw.sandbox=1");
	args.push("--label", `openclaw.sessionKey=${params.scopeKey}`);
	args.push("--label", `openclaw.createdAtMs=${createdAtMs}`);
	if (params.configHash) args.push("--label", `openclaw.configHash=${params.configHash}`);
	for (const [key, value] of Object.entries(params.labels ?? {})) if (key && value) args.push("--label", `${key}=${value}`);
	if (params.cfg.readOnlyRoot) args.push("--read-only");
	for (const entry of params.cfg.tmpfs) args.push("--tmpfs", entry);
	if (params.cfg.network) args.push("--network", params.cfg.network);
	if (params.cfg.user) args.push("--user", params.cfg.user);
	for (const [key, value] of Object.entries(params.cfg.env ?? {})) {
		if (!key.trim()) continue;
		args.push("--env", key + "=" + value);
	}
	for (const cap of params.cfg.capDrop) args.push("--cap-drop", cap);
	args.push("--security-opt", "no-new-privileges");
	if (params.cfg.seccompProfile) args.push("--security-opt", `seccomp=${params.cfg.seccompProfile}`);
	if (params.cfg.apparmorProfile) args.push("--security-opt", `apparmor=${params.cfg.apparmorProfile}`);
	for (const entry of params.cfg.dns ?? []) if (entry.trim()) args.push("--dns", entry);
	for (const entry of params.cfg.extraHosts ?? []) if (entry.trim()) args.push("--add-host", entry);
	if (typeof params.cfg.pidsLimit === "number" && params.cfg.pidsLimit > 0) args.push("--pids-limit", String(params.cfg.pidsLimit));
	const memory = normalizeDockerLimit(params.cfg.memory);
	if (memory) args.push("--memory", memory);
	const memorySwap = normalizeDockerLimit(params.cfg.memorySwap);
	if (memorySwap) args.push("--memory-swap", memorySwap);
	if (typeof params.cfg.cpus === "number" && params.cfg.cpus > 0) args.push("--cpus", String(params.cfg.cpus));
	for (const [name, value] of Object.entries(params.cfg.ulimits ?? {})) {
		const formatted = formatUlimitValue(name, value);
		if (formatted) args.push("--ulimit", formatted);
	}
	if (params.cfg.binds?.length) for (const bind of params.cfg.binds) args.push("-v", bind);
	return args;
}
async function createSandboxContainer(params) {
	const { name, cfg, workspaceDir, scopeKey } = params;
	await ensureDockerImage(cfg.image);
	const args = buildSandboxCreateArgs({
		name,
		cfg,
		scopeKey,
		configHash: params.configHash
	});
	args.push("--workdir", cfg.workdir);
	const mainMountSuffix = params.workspaceAccess === "ro" && workspaceDir === params.agentWorkspaceDir ? ":ro" : "";
	args.push("-v", `${workspaceDir}:${cfg.workdir}${mainMountSuffix}`);
	if (params.workspaceAccess !== "none" && workspaceDir !== params.agentWorkspaceDir) {
		const agentMountSuffix = params.workspaceAccess === "ro" ? ":ro" : "";
		args.push("-v", `${params.agentWorkspaceDir}:${SANDBOX_AGENT_WORKSPACE_MOUNT}${agentMountSuffix}`);
	}
	args.push(cfg.image, "sleep", "infinity");
	await execDocker(args);
	await execDocker(["start", name]);
	if (cfg.setupCommand?.trim()) await execDocker([
		"exec",
		"-i",
		name,
		"sh",
		"-lc",
		cfg.setupCommand
	]);
}
async function readContainerConfigHash(containerName) {
	const readLabel = async (label) => {
		const result = await execDocker([
			"inspect",
			"-f",
			`{{ index .Config.Labels "${label}" }}`,
			containerName
		], { allowFailure: true });
		if (result.code !== 0) return null;
		const raw = result.stdout.trim();
		if (!raw || raw === "<no value>") return null;
		return raw;
	};
	return await readLabel("openclaw.configHash");
}
function formatSandboxRecreateHint(params) {
	if (params.scope === "session") return formatCliCommand(`openclaw sandbox recreate --session ${params.sessionKey}`);
	if (params.scope === "agent") return formatCliCommand(`openclaw sandbox recreate --agent ${resolveSandboxAgentId(params.sessionKey) ?? "main"}`);
	return formatCliCommand("openclaw sandbox recreate --all");
}
async function ensureSandboxContainer(params) {
	const scopeKey = resolveSandboxScopeKey(params.cfg.scope, params.sessionKey);
	const slug = params.cfg.scope === "shared" ? "shared" : slugifySessionKey(scopeKey);
	const containerName = `${params.cfg.docker.containerPrefix}${slug}`.slice(0, 63);
	const expectedHash = computeSandboxConfigHash({
		docker: params.cfg.docker,
		workspaceAccess: params.cfg.workspaceAccess,
		workspaceDir: params.workspaceDir,
		agentWorkspaceDir: params.agentWorkspaceDir
	});
	const now = Date.now();
	const state = await dockerContainerState(containerName);
	let hasContainer = state.exists;
	let running = state.running;
	let currentHash = null;
	let hashMismatch = false;
	let registryEntry;
	if (hasContainer) {
		registryEntry = (await readRegistry()).entries.find((entry) => entry.containerName === containerName);
		currentHash = await readContainerConfigHash(containerName);
		if (!currentHash) currentHash = registryEntry?.configHash ?? null;
		hashMismatch = !currentHash || currentHash !== expectedHash;
		if (hashMismatch) {
			const lastUsedAtMs = registryEntry?.lastUsedAtMs;
			if (running && (typeof lastUsedAtMs !== "number" || now - lastUsedAtMs < HOT_CONTAINER_WINDOW_MS)) {
				const hint = formatSandboxRecreateHint({
					scope: params.cfg.scope,
					sessionKey: scopeKey
				});
				defaultRuntime.log(`Sandbox config changed for ${containerName} (recently used). Recreate to apply: ${hint}`);
			} else {
				await execDocker([
					"rm",
					"-f",
					containerName
				], { allowFailure: true });
				hasContainer = false;
				running = false;
			}
		}
	}
	if (!hasContainer) await createSandboxContainer({
		name: containerName,
		cfg: params.cfg.docker,
		workspaceDir: params.workspaceDir,
		workspaceAccess: params.cfg.workspaceAccess,
		agentWorkspaceDir: params.agentWorkspaceDir,
		scopeKey,
		configHash: expectedHash
	});
	else if (!running) await execDocker(["start", containerName]);
	await updateRegistry({
		containerName,
		sessionKey: scopeKey,
		createdAtMs: now,
		lastUsedAtMs: now,
		image: params.cfg.docker.image,
		configHash: hashMismatch && running ? currentHash ?? void 0 : expectedHash
	});
	return containerName;
}

//#endregion
//#region src/agents/sandbox/browser.ts
async function waitForSandboxCdp(params) {
	const deadline = Date.now() + Math.max(0, params.timeoutMs);
	const url = `http://127.0.0.1:${params.cdpPort}/json/version`;
	while (Date.now() < deadline) {
		try {
			const ctrl = new AbortController();
			const t = setTimeout(ctrl.abort.bind(ctrl), 1e3);
			try {
				if ((await fetch(url, { signal: ctrl.signal })).ok) return true;
			} finally {
				clearTimeout(t);
			}
		} catch {}
		await new Promise((r) => setTimeout(r, 150));
	}
	return false;
}
function buildSandboxBrowserResolvedConfig(params) {
	return {
		enabled: true,
		evaluateEnabled: params.evaluateEnabled,
		controlPort: params.controlPort,
		cdpProtocol: "http",
		cdpHost: "127.0.0.1",
		cdpIsLoopback: true,
		remoteCdpTimeoutMs: 1500,
		remoteCdpHandshakeTimeoutMs: 3e3,
		color: DEFAULT_OPENCLAW_BROWSER_COLOR,
		executablePath: void 0,
		headless: params.headless,
		noSandbox: false,
		attachOnly: true,
		defaultProfile: DEFAULT_OPENCLAW_BROWSER_PROFILE_NAME,
		profiles: { [DEFAULT_OPENCLAW_BROWSER_PROFILE_NAME]: {
			cdpPort: params.cdpPort,
			color: DEFAULT_OPENCLAW_BROWSER_COLOR
		} }
	};
}
async function ensureSandboxBrowserImage(image) {
	if ((await execDocker([
		"image",
		"inspect",
		image
	], { allowFailure: true })).code === 0) return;
	throw new Error(`Sandbox browser image not found: ${image}. Build it with scripts/sandbox-browser-setup.sh.`);
}
async function ensureSandboxBrowser(params) {
	if (!params.cfg.browser.enabled) return null;
	if (!isToolAllowed(params.cfg.tools, "browser")) return null;
	const slug = params.cfg.scope === "shared" ? "shared" : slugifySessionKey(params.scopeKey);
	const containerName = `${params.cfg.browser.containerPrefix}${slug}`.slice(0, 63);
	const state = await dockerContainerState(containerName);
	if (!state.exists) {
		await ensureSandboxBrowserImage(params.cfg.browser.image ?? DEFAULT_SANDBOX_BROWSER_IMAGE);
		const args = buildSandboxCreateArgs({
			name: containerName,
			cfg: {
				...params.cfg.docker,
				network: "bridge"
			},
			scopeKey: params.scopeKey,
			labels: { "openclaw.sandboxBrowser": "1" }
		});
		const mainMountSuffix = params.cfg.workspaceAccess === "ro" && params.workspaceDir === params.agentWorkspaceDir ? ":ro" : "";
		args.push("-v", `${params.workspaceDir}:${params.cfg.docker.workdir}${mainMountSuffix}`);
		if (params.cfg.workspaceAccess !== "none" && params.workspaceDir !== params.agentWorkspaceDir) {
			const agentMountSuffix = params.cfg.workspaceAccess === "ro" ? ":ro" : "";
			args.push("-v", `${params.agentWorkspaceDir}:${SANDBOX_AGENT_WORKSPACE_MOUNT}${agentMountSuffix}`);
		}
		args.push("-p", `127.0.0.1::${params.cfg.browser.cdpPort}`);
		if (params.cfg.browser.enableNoVnc && !params.cfg.browser.headless) args.push("-p", `127.0.0.1::${params.cfg.browser.noVncPort}`);
		args.push("-e", `OPENCLAW_BROWSER_HEADLESS=${params.cfg.browser.headless ? "1" : "0"}`);
		args.push("-e", `OPENCLAW_BROWSER_ENABLE_NOVNC=${params.cfg.browser.enableNoVnc ? "1" : "0"}`);
		args.push("-e", `OPENCLAW_BROWSER_CDP_PORT=${params.cfg.browser.cdpPort}`);
		args.push("-e", `OPENCLAW_BROWSER_VNC_PORT=${params.cfg.browser.vncPort}`);
		args.push("-e", `OPENCLAW_BROWSER_NOVNC_PORT=${params.cfg.browser.noVncPort}`);
		args.push(params.cfg.browser.image);
		await execDocker(args);
		await execDocker(["start", containerName]);
	} else if (!state.running) await execDocker(["start", containerName]);
	const mappedCdp = await readDockerPort(containerName, params.cfg.browser.cdpPort);
	if (!mappedCdp) throw new Error(`Failed to resolve CDP port mapping for ${containerName}.`);
	const mappedNoVnc = params.cfg.browser.enableNoVnc && !params.cfg.browser.headless ? await readDockerPort(containerName, params.cfg.browser.noVncPort) : null;
	const existing = BROWSER_BRIDGES.get(params.scopeKey);
	const existingProfile = existing ? resolveProfile(existing.bridge.state.resolved, DEFAULT_OPENCLAW_BROWSER_PROFILE_NAME) : null;
	const shouldReuse = existing && existing.containerName === containerName && existingProfile?.cdpPort === mappedCdp;
	if (existing && !shouldReuse) {
		await stopBrowserBridgeServer(existing.bridge.server).catch(() => void 0);
		BROWSER_BRIDGES.delete(params.scopeKey);
	}
	const bridge = (() => {
		if (shouldReuse && existing) return existing.bridge;
		return null;
	})();
	const ensureBridge = async () => {
		if (bridge) return bridge;
		const onEnsureAttachTarget = params.cfg.browser.autoStart ? async () => {
			const state = await dockerContainerState(containerName);
			if (state.exists && !state.running) await execDocker(["start", containerName]);
			if (!await waitForSandboxCdp({
				cdpPort: mappedCdp,
				timeoutMs: params.cfg.browser.autoStartTimeoutMs
			})) throw new Error(`Sandbox browser CDP did not become reachable on 127.0.0.1:${mappedCdp} within ${params.cfg.browser.autoStartTimeoutMs}ms.`);
		} : void 0;
		return await startBrowserBridgeServer({
			resolved: buildSandboxBrowserResolvedConfig({
				controlPort: 0,
				cdpPort: mappedCdp,
				headless: params.cfg.browser.headless,
				evaluateEnabled: params.evaluateEnabled ?? DEFAULT_BROWSER_EVALUATE_ENABLED
			}),
			onEnsureAttachTarget
		});
	};
	const resolvedBridge = await ensureBridge();
	if (!shouldReuse) BROWSER_BRIDGES.set(params.scopeKey, {
		bridge: resolvedBridge,
		containerName
	});
	const now = Date.now();
	await updateBrowserRegistry({
		containerName,
		sessionKey: params.scopeKey,
		createdAtMs: now,
		lastUsedAtMs: now,
		image: params.cfg.browser.image,
		cdpPort: mappedCdp,
		noVncPort: mappedNoVnc ?? void 0
	});
	const noVncUrl = mappedNoVnc && params.cfg.browser.enableNoVnc && !params.cfg.browser.headless ? `http://127.0.0.1:${mappedNoVnc}/vnc.html?autoconnect=1&resize=remote` : void 0;
	return {
		bridgeUrl: resolvedBridge.baseUrl,
		noVncUrl,
		containerName
	};
}

//#endregion
//#region src/agents/sandbox/fs-bridge.ts
function createSandboxFsBridge(params) {
	return new SandboxFsBridgeImpl(params.sandbox);
}
var SandboxFsBridgeImpl = class {
	constructor(sandbox) {
		this.sandbox = sandbox;
	}
	resolvePath(params) {
		return resolveSandboxFsPath({
			sandbox: this.sandbox,
			filePath: params.filePath,
			cwd: params.cwd
		});
	}
	async readFile(params) {
		const target = this.resolvePath(params);
		return (await this.runCommand("set -eu; cat -- \"$1\"", {
			args: [target.containerPath],
			signal: params.signal
		})).stdout;
	}
	async writeFile(params) {
		this.ensureWriteAccess("write files");
		const target = this.resolvePath(params);
		const buffer = Buffer.isBuffer(params.data) ? params.data : Buffer.from(params.data, params.encoding ?? "utf8");
		const script = params.mkdir === false ? "set -eu; cat >\"$1\"" : "set -eu; dir=$(dirname -- \"$1\"); if [ \"$dir\" != \".\" ]; then mkdir -p -- \"$dir\"; fi; cat >\"$1\"";
		await this.runCommand(script, {
			args: [target.containerPath],
			stdin: buffer,
			signal: params.signal
		});
	}
	async mkdirp(params) {
		this.ensureWriteAccess("create directories");
		const target = this.resolvePath(params);
		await this.runCommand("set -eu; mkdir -p -- \"$1\"", {
			args: [target.containerPath],
			signal: params.signal
		});
	}
	async remove(params) {
		this.ensureWriteAccess("remove files");
		const target = this.resolvePath(params);
		const flags = [params.force === false ? "" : "-f", params.recursive ? "-r" : ""].filter(Boolean);
		const rmCommand = flags.length > 0 ? `rm ${flags.join(" ")}` : "rm";
		await this.runCommand(`set -eu; ${rmCommand} -- "$1"`, {
			args: [target.containerPath],
			signal: params.signal
		});
	}
	async rename(params) {
		this.ensureWriteAccess("rename files");
		const from = this.resolvePath({
			filePath: params.from,
			cwd: params.cwd
		});
		const to = this.resolvePath({
			filePath: params.to,
			cwd: params.cwd
		});
		await this.runCommand("set -eu; dir=$(dirname -- \"$2\"); if [ \"$dir\" != \".\" ]; then mkdir -p -- \"$dir\"; fi; mv -- \"$1\" \"$2\"", {
			args: [from.containerPath, to.containerPath],
			signal: params.signal
		});
	}
	async stat(params) {
		const target = this.resolvePath(params);
		const result = await this.runCommand("set -eu; stat -c \"%F|%s|%Y\" -- \"$1\"", {
			args: [target.containerPath],
			signal: params.signal,
			allowFailure: true
		});
		if (result.code !== 0) {
			const stderr = result.stderr.toString("utf8");
			if (stderr.includes("No such file or directory")) return null;
			const message = stderr.trim() || `stat failed with code ${result.code}`;
			throw new Error(`stat failed for ${target.containerPath}: ${message}`);
		}
		const [typeRaw, sizeRaw, mtimeRaw] = result.stdout.toString("utf8").trim().split("|");
		const size = Number.parseInt(sizeRaw ?? "0", 10);
		const mtime = Number.parseInt(mtimeRaw ?? "0", 10) * 1e3;
		return {
			type: coerceStatType(typeRaw),
			size: Number.isFinite(size) ? size : 0,
			mtimeMs: Number.isFinite(mtime) ? mtime : 0
		};
	}
	async runCommand(script, options = {}) {
		const dockerArgs = [
			"exec",
			"-i",
			this.sandbox.containerName,
			"sh",
			"-c",
			script,
			"moltbot-sandbox-fs"
		];
		if (options.args?.length) dockerArgs.push(...options.args);
		return execDockerRaw(dockerArgs, {
			input: options.stdin,
			allowFailure: options.allowFailure,
			signal: options.signal
		});
	}
	ensureWriteAccess(action) {
		if (!allowsWrites(this.sandbox.workspaceAccess)) throw new Error(`Sandbox workspace (${this.sandbox.workspaceAccess}) does not allow ${action}.`);
	}
};
function allowsWrites(access) {
	return access === "rw";
}
function resolveSandboxFsPath(params) {
	const root = params.sandbox.workspaceDir;
	const cwd = params.cwd ?? root;
	const { resolved, relative } = resolveSandboxPath({
		filePath: params.filePath,
		cwd,
		root
	});
	const normalizedRelative = relative ? relative.split(path.sep).filter(Boolean).join(path.posix.sep) : "";
	return {
		hostPath: resolved,
		relativePath: normalizedRelative,
		containerPath: normalizedRelative ? path.posix.join(params.sandbox.containerWorkdir, normalizedRelative) : params.sandbox.containerWorkdir
	};
}
function coerceStatType(typeRaw) {
	if (!typeRaw) return "other";
	const normalized = typeRaw.trim().toLowerCase();
	if (normalized.includes("directory")) return "directory";
	if (normalized.includes("file")) return "file";
	return "other";
}

//#endregion
//#region src/agents/sandbox/prune.ts
let lastPruneAtMs = 0;
async function pruneSandboxContainers(cfg) {
	const now = Date.now();
	const idleHours = cfg.prune.idleHours;
	const maxAgeDays = cfg.prune.maxAgeDays;
	if (idleHours === 0 && maxAgeDays === 0) return;
	const registry = await readRegistry();
	for (const entry of registry.entries) {
		const idleMs = now - entry.lastUsedAtMs;
		const ageMs = now - entry.createdAtMs;
		if (idleHours > 0 && idleMs > idleHours * 60 * 60 * 1e3 || maxAgeDays > 0 && ageMs > maxAgeDays * 24 * 60 * 60 * 1e3) try {
			await execDocker([
				"rm",
				"-f",
				entry.containerName
			], { allowFailure: true });
		} catch {} finally {
			await removeRegistryEntry(entry.containerName);
		}
	}
}
async function pruneSandboxBrowsers(cfg) {
	const now = Date.now();
	const idleHours = cfg.prune.idleHours;
	const maxAgeDays = cfg.prune.maxAgeDays;
	if (idleHours === 0 && maxAgeDays === 0) return;
	const registry = await readBrowserRegistry();
	for (const entry of registry.entries) {
		const idleMs = now - entry.lastUsedAtMs;
		const ageMs = now - entry.createdAtMs;
		if (idleHours > 0 && idleMs > idleHours * 60 * 60 * 1e3 || maxAgeDays > 0 && ageMs > maxAgeDays * 24 * 60 * 60 * 1e3) try {
			await execDocker([
				"rm",
				"-f",
				entry.containerName
			], { allowFailure: true });
		} catch {} finally {
			await removeBrowserRegistryEntry(entry.containerName);
			const bridge = BROWSER_BRIDGES.get(entry.sessionKey);
			if (bridge?.containerName === entry.containerName) {
				await stopBrowserBridgeServer(bridge.bridge.server).catch(() => void 0);
				BROWSER_BRIDGES.delete(entry.sessionKey);
			}
		}
	}
}
async function maybePruneSandboxes(cfg) {
	const now = Date.now();
	if (now - lastPruneAtMs < 300 * 1e3) return;
	lastPruneAtMs = now;
	try {
		await pruneSandboxContainers(cfg);
		await pruneSandboxBrowsers(cfg);
	} catch (error) {
		const message = error instanceof Error ? error.message : typeof error === "string" ? error : JSON.stringify(error);
		defaultRuntime.error?.(`Sandbox prune failed: ${message ?? "unknown error"}`);
	}
}

//#endregion
//#region src/config/sessions/group.ts
const getGroupSurfaces = () => new Set([...listDeliverableMessageChannels(), "webchat"]);
function normalizeGroupLabel(raw) {
	const trimmed = raw?.trim().toLowerCase() ?? "";
	if (!trimmed) return "";
	return trimmed.replace(/\s+/g, "-").replace(/[^a-z0-9#@._+-]+/g, "-").replace(/-{2,}/g, "-").replace(/^[-.]+|[-.]+$/g, "");
}
function shortenGroupId(value) {
	const trimmed = value?.trim() ?? "";
	if (!trimmed) return "";
	if (trimmed.length <= 14) return trimmed;
	return `${trimmed.slice(0, 6)}...${trimmed.slice(-4)}`;
}
function buildGroupDisplayName(params) {
	const providerKey = (params.provider?.trim().toLowerCase() || "group").trim();
	const groupChannel = params.groupChannel?.trim();
	const space = params.space?.trim();
	const subject = params.subject?.trim();
	const detail = (groupChannel && space ? `${space}${groupChannel.startsWith("#") ? "" : "#"}${groupChannel}` : groupChannel || subject || space || "") || "";
	const fallbackId = params.id?.trim() || params.key;
	const rawLabel = detail || fallbackId;
	let token = normalizeGroupLabel(rawLabel);
	if (!token) token = normalizeGroupLabel(shortenGroupId(rawLabel));
	if (!params.groupChannel && token.startsWith("#")) token = token.replace(/^#+/, "");
	if (token && !/^[@#]/.test(token) && !token.startsWith("g-") && !token.includes("#")) token = `g-${token}`;
	return token ? `${providerKey}:${token}` : providerKey;
}
function resolveGroupSessionKey(ctx) {
	const from = typeof ctx.From === "string" ? ctx.From.trim() : "";
	const chatType = ctx.ChatType?.trim().toLowerCase();
	const normalizedChatType = chatType === "channel" ? "channel" : chatType === "group" ? "group" : void 0;
	const isWhatsAppGroupId = from.toLowerCase().endsWith("@g.us");
	if (!(normalizedChatType === "group" || normalizedChatType === "channel" || from.includes(":group:") || from.includes(":channel:") || isWhatsAppGroupId)) return null;
	const providerHint = ctx.Provider?.trim().toLowerCase();
	const parts = from.split(":").filter(Boolean);
	const head = parts[0]?.trim().toLowerCase() ?? "";
	const headIsSurface = head ? getGroupSurfaces().has(head) : false;
	const provider = headIsSurface ? head : providerHint ?? (isWhatsAppGroupId ? "whatsapp" : void 0);
	if (!provider) return null;
	const second = parts[1]?.trim().toLowerCase();
	const secondIsKind = second === "group" || second === "channel";
	const kind = secondIsKind ? second : from.includes(":channel:") || normalizedChatType === "channel" ? "channel" : "group";
	const finalId = (headIsSurface ? secondIsKind ? parts.slice(2).join(":") : parts.slice(1).join(":") : from).trim().toLowerCase();
	if (!finalId) return null;
	return {
		key: `${provider}:${kind}:${finalId}`,
		channel: provider,
		id: finalId,
		chatType: kind === "channel" ? "channel" : "group"
	};
}

//#endregion
//#region src/config/group-policy.ts
function resolveChannelGroupConfig(groups, groupId, caseInsensitive = false) {
	if (!groups) return;
	const direct = groups[groupId];
	if (direct) return direct;
	if (!caseInsensitive) return;
	const target = groupId.toLowerCase();
	const matchedKey = Object.keys(groups).find((key) => key !== "*" && key.toLowerCase() === target);
	if (!matchedKey) return;
	return groups[matchedKey];
}
function normalizeSenderKey(value) {
	const trimmed = value.trim();
	if (!trimmed) return "";
	return (trimmed.startsWith("@") ? trimmed.slice(1) : trimmed).toLowerCase();
}
function resolveToolsBySender(params) {
	const toolsBySender = params.toolsBySender;
	if (!toolsBySender) return;
	const entries = Object.entries(toolsBySender);
	if (entries.length === 0) return;
	const normalized = /* @__PURE__ */ new Map();
	let wildcard;
	for (const [rawKey, policy] of entries) {
		if (!policy) continue;
		const key = normalizeSenderKey(rawKey);
		if (!key) continue;
		if (key === "*") {
			wildcard = policy;
			continue;
		}
		if (!normalized.has(key)) normalized.set(key, policy);
	}
	const candidates = [];
	const pushCandidate = (value) => {
		const trimmed = value?.trim();
		if (!trimmed) return;
		candidates.push(trimmed);
	};
	pushCandidate(params.senderId);
	pushCandidate(params.senderE164);
	pushCandidate(params.senderUsername);
	pushCandidate(params.senderName);
	for (const candidate of candidates) {
		const key = normalizeSenderKey(candidate);
		if (!key) continue;
		const match = normalized.get(key);
		if (match) return match;
	}
	return wildcard;
}
function resolveChannelGroups(cfg, channel, accountId) {
	const normalizedAccountId = normalizeAccountId$1(accountId);
	const channelConfig = cfg.channels?.[channel];
	if (!channelConfig) return;
	return channelConfig.accounts?.[normalizedAccountId]?.groups ?? channelConfig.accounts?.[Object.keys(channelConfig.accounts ?? {}).find((key) => key.toLowerCase() === normalizedAccountId.toLowerCase()) ?? ""]?.groups ?? channelConfig.groups;
}
function resolveChannelGroupPolicy(params) {
	const { cfg, channel } = params;
	const groups = resolveChannelGroups(cfg, channel, params.accountId);
	const allowlistEnabled = Boolean(groups && Object.keys(groups).length > 0);
	const normalizedId = params.groupId?.trim();
	const groupConfig = normalizedId ? resolveChannelGroupConfig(groups, normalizedId, params.groupIdCaseInsensitive) : void 0;
	const defaultConfig = groups?.["*"];
	return {
		allowlistEnabled,
		allowed: !allowlistEnabled || allowlistEnabled && Boolean(groups && Object.hasOwn(groups, "*")) || Boolean(groupConfig),
		groupConfig,
		defaultConfig
	};
}
function resolveChannelGroupRequireMention(params) {
	const { requireMentionOverride, overrideOrder = "after-config" } = params;
	const { groupConfig, defaultConfig } = resolveChannelGroupPolicy(params);
	const configMention = typeof groupConfig?.requireMention === "boolean" ? groupConfig.requireMention : typeof defaultConfig?.requireMention === "boolean" ? defaultConfig.requireMention : void 0;
	if (overrideOrder === "before-config" && typeof requireMentionOverride === "boolean") return requireMentionOverride;
	if (typeof configMention === "boolean") return configMention;
	if (overrideOrder !== "before-config" && typeof requireMentionOverride === "boolean") return requireMentionOverride;
	return true;
}
function resolveChannelGroupToolsPolicy(params) {
	const { groupConfig, defaultConfig } = resolveChannelGroupPolicy(params);
	const groupSenderPolicy = resolveToolsBySender({
		toolsBySender: groupConfig?.toolsBySender,
		senderId: params.senderId,
		senderName: params.senderName,
		senderUsername: params.senderUsername,
		senderE164: params.senderE164
	});
	if (groupSenderPolicy) return groupSenderPolicy;
	if (groupConfig?.tools) return groupConfig.tools;
	const defaultSenderPolicy = resolveToolsBySender({
		toolsBySender: defaultConfig?.toolsBySender,
		senderId: params.senderId,
		senderName: params.senderName,
		senderUsername: params.senderUsername,
		senderE164: params.senderE164
	});
	if (defaultSenderPolicy) return defaultSenderPolicy;
	if (defaultConfig?.tools) return defaultConfig.tools;
}

//#endregion
//#region src/imessage/accounts.ts
function resolveAccountConfig$1(cfg, accountId) {
	const accounts = cfg.channels?.imessage?.accounts;
	if (!accounts || typeof accounts !== "object") return;
	return accounts[accountId];
}
function mergeIMessageAccountConfig(cfg, accountId) {
	const { accounts: _ignored, ...base } = cfg.channels?.imessage ?? {};
	const account = resolveAccountConfig$1(cfg, accountId) ?? {};
	return {
		...base,
		...account
	};
}
function resolveIMessageAccount(params) {
	const accountId = normalizeAccountId$1(params.accountId);
	const baseEnabled = params.cfg.channels?.imessage?.enabled !== false;
	const merged = mergeIMessageAccountConfig(params.cfg, accountId);
	const accountEnabled = merged.enabled !== false;
	const configured = Boolean(merged.cliPath?.trim() || merged.dbPath?.trim() || merged.service || merged.region?.trim() || merged.allowFrom && merged.allowFrom.length > 0 || merged.groupAllowFrom && merged.groupAllowFrom.length > 0 || merged.dmPolicy || merged.groupPolicy || typeof merged.includeAttachments === "boolean" || typeof merged.mediaMaxMb === "number" || typeof merged.textChunkLimit === "number" || merged.groups && Object.keys(merged.groups).length > 0);
	return {
		accountId,
		enabled: baseEnabled && accountEnabled,
		name: merged.name?.trim() || void 0,
		config: merged,
		configured
	};
}

//#endregion
//#region src/signal/accounts.ts
function listConfiguredAccountIds(cfg) {
	const accounts = cfg.channels?.signal?.accounts;
	if (!accounts || typeof accounts !== "object") return [];
	return Object.keys(accounts).filter(Boolean);
}
function listSignalAccountIds(cfg) {
	const ids = listConfiguredAccountIds(cfg);
	if (ids.length === 0) return [DEFAULT_ACCOUNT_ID];
	return ids.toSorted((a, b) => a.localeCompare(b));
}
function resolveAccountConfig(cfg, accountId) {
	const accounts = cfg.channels?.signal?.accounts;
	if (!accounts || typeof accounts !== "object") return;
	return accounts[accountId];
}
function mergeSignalAccountConfig(cfg, accountId) {
	const { accounts: _ignored, ...base } = cfg.channels?.signal ?? {};
	const account = resolveAccountConfig(cfg, accountId) ?? {};
	return {
		...base,
		...account
	};
}
function resolveSignalAccount(params) {
	const accountId = normalizeAccountId$1(params.accountId);
	const baseEnabled = params.cfg.channels?.signal?.enabled !== false;
	const merged = mergeSignalAccountConfig(params.cfg, accountId);
	const accountEnabled = merged.enabled !== false;
	const enabled = baseEnabled && accountEnabled;
	const host = merged.httpHost?.trim() || "127.0.0.1";
	const port = merged.httpPort ?? 8080;
	const baseUrl = merged.httpUrl?.trim() || `http://${host}:${port}`;
	const configured = Boolean(merged.account?.trim() || merged.httpUrl?.trim() || merged.cliPath?.trim() || merged.httpHost?.trim() || typeof merged.httpPort === "number" || typeof merged.autoStart === "boolean");
	return {
		accountId,
		enabled,
		name: merged.name?.trim() || void 0,
		baseUrl,
		configured,
		config: merged
	};
}
function listEnabledSignalAccounts(cfg) {
	return listSignalAccountIds(cfg).map((accountId) => resolveSignalAccount({
		cfg,
		accountId
	})).filter((account) => account.enabled);
}

//#endregion
//#region src/slack/threading-tool-context.ts
function buildSlackThreadingToolContext(params) {
	const configuredReplyToMode = resolveSlackReplyToMode(resolveSlackAccount({
		cfg: params.cfg,
		accountId: params.accountId
	}), params.context.ChatType);
	const effectiveReplyToMode = params.context.ThreadLabel ? "all" : configuredReplyToMode;
	const threadId = params.context.MessageThreadId ?? params.context.ReplyToId;
	return {
		currentChannelId: params.context.To?.startsWith("channel:") ? params.context.To.slice(8) : void 0,
		currentThreadTs: threadId != null ? String(threadId) : void 0,
		replyToMode: effectiveReplyToMode,
		hasRepliedRef: params.hasRepliedRef
	};
}

//#endregion
//#region src/channels/plugins/group-mentions.ts
function normalizeDiscordSlug(value) {
	if (!value) return "";
	let text = value.trim().toLowerCase();
	if (!text) return "";
	text = text.replace(/^[@#]+/, "");
	text = text.replace(/[\s_]+/g, "-");
	text = text.replace(/[^a-z0-9-]+/g, "-");
	text = text.replace(/-{2,}/g, "-").replace(/^-+|-+$/g, "");
	return text;
}
function normalizeSlackSlug(raw) {
	const trimmed = raw?.trim().toLowerCase() ?? "";
	if (!trimmed) return "";
	return trimmed.replace(/\s+/g, "-").replace(/[^a-z0-9#@._+-]+/g, "-").replace(/-{2,}/g, "-").replace(/^[-.]+|[-.]+$/g, "");
}
function parseTelegramGroupId(value) {
	const raw = value?.trim() ?? "";
	if (!raw) return {
		chatId: void 0,
		topicId: void 0
	};
	const parts = raw.split(":").filter(Boolean);
	if (parts.length >= 3 && parts[1] === "topic" && /^-?\d+$/.test(parts[0]) && /^\d+$/.test(parts[2])) return {
		chatId: parts[0],
		topicId: parts[2]
	};
	if (parts.length >= 2 && /^-?\d+$/.test(parts[0]) && /^\d+$/.test(parts[1])) return {
		chatId: parts[0],
		topicId: parts[1]
	};
	return {
		chatId: raw,
		topicId: void 0
	};
}
function resolveTelegramRequireMention(params) {
	const { cfg, chatId, topicId } = params;
	if (!chatId) return;
	const groupConfig = cfg.channels?.telegram?.groups?.[chatId];
	const groupDefault = cfg.channels?.telegram?.groups?.["*"];
	const topicConfig = topicId && groupConfig?.topics ? groupConfig.topics[topicId] : void 0;
	const defaultTopicConfig = topicId && groupDefault?.topics ? groupDefault.topics[topicId] : void 0;
	if (typeof topicConfig?.requireMention === "boolean") return topicConfig.requireMention;
	if (typeof defaultTopicConfig?.requireMention === "boolean") return defaultTopicConfig.requireMention;
	if (typeof groupConfig?.requireMention === "boolean") return groupConfig.requireMention;
	if (typeof groupDefault?.requireMention === "boolean") return groupDefault.requireMention;
}
function resolveDiscordGuildEntry(guilds, groupSpace) {
	if (!guilds || Object.keys(guilds).length === 0) return null;
	const space = groupSpace?.trim() ?? "";
	if (space && guilds[space]) return guilds[space];
	const normalized = normalizeDiscordSlug(space);
	if (normalized && guilds[normalized]) return guilds[normalized];
	if (normalized) {
		const match = Object.values(guilds).find((entry) => normalizeDiscordSlug(entry?.slug ?? void 0) === normalized);
		if (match) return match;
	}
	return guilds["*"] ?? null;
}
function resolveTelegramGroupRequireMention(params) {
	const { chatId, topicId } = parseTelegramGroupId(params.groupId);
	const requireMention = resolveTelegramRequireMention({
		cfg: params.cfg,
		chatId,
		topicId
	});
	if (typeof requireMention === "boolean") return requireMention;
	return resolveChannelGroupRequireMention({
		cfg: params.cfg,
		channel: "telegram",
		groupId: chatId ?? params.groupId,
		accountId: params.accountId
	});
}
function resolveWhatsAppGroupRequireMention(params) {
	return resolveChannelGroupRequireMention({
		cfg: params.cfg,
		channel: "whatsapp",
		groupId: params.groupId,
		accountId: params.accountId
	});
}
function resolveIMessageGroupRequireMention(params) {
	return resolveChannelGroupRequireMention({
		cfg: params.cfg,
		channel: "imessage",
		groupId: params.groupId,
		accountId: params.accountId
	});
}
function resolveDiscordGroupRequireMention(params) {
	const guildEntry = resolveDiscordGuildEntry(params.cfg.channels?.discord?.guilds, params.groupSpace);
	const channelEntries = guildEntry?.channels;
	if (channelEntries && Object.keys(channelEntries).length > 0) {
		const groupChannel = params.groupChannel;
		const channelSlug = normalizeDiscordSlug(groupChannel);
		const entry = (params.groupId ? channelEntries[params.groupId] : void 0) ?? (channelSlug ? channelEntries[channelSlug] ?? channelEntries[`#${channelSlug}`] : void 0) ?? (groupChannel ? channelEntries[normalizeDiscordSlug(groupChannel)] : void 0);
		if (entry && typeof entry.requireMention === "boolean") return entry.requireMention;
	}
	if (typeof guildEntry?.requireMention === "boolean") return guildEntry.requireMention;
	return true;
}
function resolveGoogleChatGroupRequireMention(params) {
	return resolveChannelGroupRequireMention({
		cfg: params.cfg,
		channel: "googlechat",
		groupId: params.groupId,
		accountId: params.accountId
	});
}
function resolveGoogleChatGroupToolPolicy(params) {
	return resolveChannelGroupToolsPolicy({
		cfg: params.cfg,
		channel: "googlechat",
		groupId: params.groupId,
		accountId: params.accountId,
		senderId: params.senderId,
		senderName: params.senderName,
		senderUsername: params.senderUsername,
		senderE164: params.senderE164
	});
}
function resolveSlackGroupRequireMention(params) {
	const channels = resolveSlackAccount({
		cfg: params.cfg,
		accountId: params.accountId
	}).channels ?? {};
	if (Object.keys(channels).length === 0) return true;
	const channelId = params.groupId?.trim();
	const channelName = params.groupChannel?.replace(/^#/, "");
	const normalizedName = normalizeSlackSlug(channelName);
	const candidates = [
		channelId ?? "",
		channelName ? `#${channelName}` : "",
		channelName ?? "",
		normalizedName
	].filter(Boolean);
	let matched;
	for (const candidate of candidates) if (candidate && channels[candidate]) {
		matched = channels[candidate];
		break;
	}
	const fallback = channels["*"];
	const resolved = matched ?? fallback;
	if (typeof resolved?.requireMention === "boolean") return resolved.requireMention;
	return true;
}
function resolveTelegramGroupToolPolicy(params) {
	const { chatId } = parseTelegramGroupId(params.groupId);
	return resolveChannelGroupToolsPolicy({
		cfg: params.cfg,
		channel: "telegram",
		groupId: chatId ?? params.groupId,
		accountId: params.accountId,
		senderId: params.senderId,
		senderName: params.senderName,
		senderUsername: params.senderUsername,
		senderE164: params.senderE164
	});
}
function resolveWhatsAppGroupToolPolicy(params) {
	return resolveChannelGroupToolsPolicy({
		cfg: params.cfg,
		channel: "whatsapp",
		groupId: params.groupId,
		accountId: params.accountId,
		senderId: params.senderId,
		senderName: params.senderName,
		senderUsername: params.senderUsername,
		senderE164: params.senderE164
	});
}
function resolveIMessageGroupToolPolicy(params) {
	return resolveChannelGroupToolsPolicy({
		cfg: params.cfg,
		channel: "imessage",
		groupId: params.groupId,
		accountId: params.accountId,
		senderId: params.senderId,
		senderName: params.senderName,
		senderUsername: params.senderUsername,
		senderE164: params.senderE164
	});
}
function resolveDiscordGroupToolPolicy(params) {
	const guildEntry = resolveDiscordGuildEntry(params.cfg.channels?.discord?.guilds, params.groupSpace);
	const channelEntries = guildEntry?.channels;
	if (channelEntries && Object.keys(channelEntries).length > 0) {
		const groupChannel = params.groupChannel;
		const channelSlug = normalizeDiscordSlug(groupChannel);
		const entry = (params.groupId ? channelEntries[params.groupId] : void 0) ?? (channelSlug ? channelEntries[channelSlug] ?? channelEntries[`#${channelSlug}`] : void 0) ?? (groupChannel ? channelEntries[normalizeDiscordSlug(groupChannel)] : void 0);
		const senderPolicy = resolveToolsBySender({
			toolsBySender: entry?.toolsBySender,
			senderId: params.senderId,
			senderName: params.senderName,
			senderUsername: params.senderUsername,
			senderE164: params.senderE164
		});
		if (senderPolicy) return senderPolicy;
		if (entry?.tools) return entry.tools;
	}
	const guildSenderPolicy = resolveToolsBySender({
		toolsBySender: guildEntry?.toolsBySender,
		senderId: params.senderId,
		senderName: params.senderName,
		senderUsername: params.senderUsername,
		senderE164: params.senderE164
	});
	if (guildSenderPolicy) return guildSenderPolicy;
	if (guildEntry?.tools) return guildEntry.tools;
}
function resolveSlackGroupToolPolicy(params) {
	const channels = resolveSlackAccount({
		cfg: params.cfg,
		accountId: params.accountId
	}).channels ?? {};
	if (Object.keys(channels).length === 0) return;
	const channelId = params.groupId?.trim();
	const channelName = params.groupChannel?.replace(/^#/, "");
	const normalizedName = normalizeSlackSlug(channelName);
	const candidates = [
		channelId ?? "",
		channelName ? `#${channelName}` : "",
		channelName ?? "",
		normalizedName
	].filter(Boolean);
	let matched;
	for (const candidate of candidates) if (candidate && channels[candidate]) {
		matched = channels[candidate];
		break;
	}
	const resolved = matched ?? channels["*"];
	const senderPolicy = resolveToolsBySender({
		toolsBySender: resolved?.toolsBySender,
		senderId: params.senderId,
		senderName: params.senderName,
		senderUsername: params.senderUsername,
		senderE164: params.senderE164
	});
	if (senderPolicy) return senderPolicy;
	if (resolved?.tools) return resolved.tools;
}

//#endregion
//#region src/channels/dock.ts
const formatLower = (allowFrom) => allowFrom.map((entry) => String(entry).trim()).filter(Boolean).map((entry) => entry.toLowerCase());
const DOCKS = {
	telegram: {
		id: "telegram",
		capabilities: {
			chatTypes: [
				"direct",
				"group",
				"channel",
				"thread"
			],
			nativeCommands: true,
			blockStreaming: true
		},
		outbound: { textChunkLimit: 4e3 },
		config: {
			resolveAllowFrom: ({ cfg, accountId }) => (resolveTelegramAccount({
				cfg,
				accountId
			}).config.allowFrom ?? []).map((entry) => String(entry)),
			formatAllowFrom: ({ allowFrom }) => allowFrom.map((entry) => String(entry).trim()).filter(Boolean).map((entry) => entry.replace(/^(telegram|tg):/i, "")).map((entry) => entry.toLowerCase())
		},
		groups: {
			resolveRequireMention: resolveTelegramGroupRequireMention,
			resolveToolPolicy: resolveTelegramGroupToolPolicy
		},
		threading: {
			resolveReplyToMode: ({ cfg }) => cfg.channels?.telegram?.replyToMode ?? "first",
			buildToolContext: ({ context, hasRepliedRef }) => {
				const threadId = context.MessageThreadId ?? context.ReplyToId;
				return {
					currentChannelId: context.To?.trim() || void 0,
					currentThreadTs: threadId != null ? String(threadId) : void 0,
					hasRepliedRef
				};
			}
		}
	},
	whatsapp: {
		id: "whatsapp",
		capabilities: {
			chatTypes: ["direct", "group"],
			polls: true,
			reactions: true,
			media: true
		},
		commands: {
			enforceOwnerForCommands: true,
			skipWhenConfigEmpty: true
		},
		outbound: { textChunkLimit: 4e3 },
		config: {
			resolveAllowFrom: ({ cfg, accountId }) => resolveWhatsAppAccount({
				cfg,
				accountId
			}).allowFrom ?? [],
			formatAllowFrom: ({ allowFrom }) => allowFrom.map((entry) => String(entry).trim()).filter((entry) => Boolean(entry)).map((entry) => entry === "*" ? entry : normalizeWhatsAppTarget(entry)).filter((entry) => Boolean(entry))
		},
		groups: {
			resolveRequireMention: resolveWhatsAppGroupRequireMention,
			resolveToolPolicy: resolveWhatsAppGroupToolPolicy,
			resolveGroupIntroHint: () => "WhatsApp IDs: SenderId is the participant JID (group participant id)."
		},
		mentions: { stripPatterns: ({ ctx }) => {
			const selfE164 = (ctx.To ?? "").replace(/^whatsapp:/, "");
			if (!selfE164) return [];
			const escaped = escapeRegExp(selfE164);
			return [escaped, `@${escaped}`];
		} },
		threading: { buildToolContext: ({ context, hasRepliedRef }) => {
			return {
				currentChannelId: context.From?.trim() || context.To?.trim() || void 0,
				currentThreadTs: context.ReplyToId,
				hasRepliedRef
			};
		} }
	},
	discord: {
		id: "discord",
		capabilities: {
			chatTypes: [
				"direct",
				"channel",
				"thread"
			],
			polls: true,
			reactions: true,
			media: true,
			nativeCommands: true,
			threads: true
		},
		outbound: { textChunkLimit: 2e3 },
		streaming: { blockStreamingCoalesceDefaults: {
			minChars: 1500,
			idleMs: 1e3
		} },
		elevated: { allowFromFallback: ({ cfg }) => cfg.channels?.discord?.dm?.allowFrom },
		config: {
			resolveAllowFrom: ({ cfg, accountId }) => (resolveDiscordAccount({
				cfg,
				accountId
			}).config.dm?.allowFrom ?? []).map((entry) => String(entry)),
			formatAllowFrom: ({ allowFrom }) => formatLower(allowFrom)
		},
		groups: {
			resolveRequireMention: resolveDiscordGroupRequireMention,
			resolveToolPolicy: resolveDiscordGroupToolPolicy
		},
		mentions: { stripPatterns: () => ["<@!?\\d+>"] },
		threading: {
			resolveReplyToMode: ({ cfg }) => cfg.channels?.discord?.replyToMode ?? "off",
			buildToolContext: ({ context, hasRepliedRef }) => ({
				currentChannelId: context.To?.trim() || void 0,
				currentThreadTs: context.ReplyToId,
				hasRepliedRef
			})
		}
	},
	irc: {
		id: "irc",
		capabilities: {
			chatTypes: ["direct", "group"],
			media: true,
			blockStreaming: true
		},
		outbound: { textChunkLimit: 350 },
		streaming: { blockStreamingCoalesceDefaults: {
			minChars: 300,
			idleMs: 1e3
		} },
		config: {
			resolveAllowFrom: ({ cfg, accountId }) => {
				const channel = cfg.channels?.irc;
				const normalized = normalizeAccountId$1(accountId);
				return ((channel?.accounts?.[normalized] ?? channel?.accounts?.[Object.keys(channel?.accounts ?? {}).find((key) => key.toLowerCase() === normalized.toLowerCase()) ?? ""])?.allowFrom ?? channel?.allowFrom ?? []).map((entry) => String(entry));
			},
			formatAllowFrom: ({ allowFrom }) => allowFrom.map((entry) => String(entry).trim()).filter(Boolean).map((entry) => entry.replace(/^irc:/i, "").replace(/^user:/i, "").toLowerCase())
		},
		groups: {
			resolveRequireMention: ({ cfg, accountId, groupId }) => {
				if (!groupId) return true;
				return resolveChannelGroupRequireMention({
					cfg,
					channel: "irc",
					groupId,
					accountId,
					groupIdCaseInsensitive: true
				});
			},
			resolveToolPolicy: ({ cfg, accountId, groupId, senderId, senderName, senderUsername }) => {
				if (!groupId) return;
				return resolveChannelGroupToolsPolicy({
					cfg,
					channel: "irc",
					groupId,
					accountId,
					groupIdCaseInsensitive: true,
					senderId,
					senderName,
					senderUsername
				});
			}
		}
	},
	googlechat: {
		id: "googlechat",
		capabilities: {
			chatTypes: [
				"direct",
				"group",
				"thread"
			],
			reactions: true,
			media: true,
			threads: true,
			blockStreaming: true
		},
		outbound: { textChunkLimit: 4e3 },
		config: {
			resolveAllowFrom: ({ cfg, accountId }) => {
				const channel = cfg.channels?.googlechat;
				const normalized = normalizeAccountId$1(accountId);
				return ((channel?.accounts?.[normalized] ?? channel?.accounts?.[Object.keys(channel?.accounts ?? {}).find((key) => key.toLowerCase() === normalized.toLowerCase()) ?? ""])?.dm?.allowFrom ?? channel?.dm?.allowFrom ?? []).map((entry) => String(entry));
			},
			formatAllowFrom: ({ allowFrom }) => allowFrom.map((entry) => String(entry).trim()).filter(Boolean).map((entry) => entry.replace(/^(googlechat|google-chat|gchat):/i, "").replace(/^user:/i, "").replace(/^users\//i, "").toLowerCase())
		},
		groups: {
			resolveRequireMention: resolveGoogleChatGroupRequireMention,
			resolveToolPolicy: resolveGoogleChatGroupToolPolicy
		},
		threading: {
			resolveReplyToMode: ({ cfg }) => cfg.channels?.googlechat?.replyToMode ?? "off",
			buildToolContext: ({ context, hasRepliedRef }) => {
				const threadId = context.MessageThreadId ?? context.ReplyToId;
				return {
					currentChannelId: context.To?.trim() || void 0,
					currentThreadTs: threadId != null ? String(threadId) : void 0,
					hasRepliedRef
				};
			}
		}
	},
	slack: {
		id: "slack",
		capabilities: {
			chatTypes: [
				"direct",
				"channel",
				"thread"
			],
			reactions: true,
			media: true,
			nativeCommands: true,
			threads: true
		},
		outbound: { textChunkLimit: 4e3 },
		streaming: { blockStreamingCoalesceDefaults: {
			minChars: 1500,
			idleMs: 1e3
		} },
		config: {
			resolveAllowFrom: ({ cfg, accountId }) => (resolveSlackAccount({
				cfg,
				accountId
			}).dm?.allowFrom ?? []).map((entry) => String(entry)),
			formatAllowFrom: ({ allowFrom }) => formatLower(allowFrom)
		},
		groups: {
			resolveRequireMention: resolveSlackGroupRequireMention,
			resolveToolPolicy: resolveSlackGroupToolPolicy
		},
		mentions: { stripPatterns: () => ["<@[^>]+>"] },
		threading: {
			resolveReplyToMode: ({ cfg, accountId, chatType }) => resolveSlackReplyToMode(resolveSlackAccount({
				cfg,
				accountId
			}), chatType),
			allowTagsWhenOff: true,
			buildToolContext: (params) => buildSlackThreadingToolContext(params)
		}
	},
	signal: {
		id: "signal",
		capabilities: {
			chatTypes: ["direct", "group"],
			reactions: true,
			media: true
		},
		outbound: { textChunkLimit: 4e3 },
		streaming: { blockStreamingCoalesceDefaults: {
			minChars: 1500,
			idleMs: 1e3
		} },
		config: {
			resolveAllowFrom: ({ cfg, accountId }) => (resolveSignalAccount({
				cfg,
				accountId
			}).config.allowFrom ?? []).map((entry) => String(entry)),
			formatAllowFrom: ({ allowFrom }) => allowFrom.map((entry) => String(entry).trim()).filter(Boolean).map((entry) => entry === "*" ? "*" : normalizeE164(entry.replace(/^signal:/i, ""))).filter(Boolean)
		},
		threading: { buildToolContext: ({ context, hasRepliedRef }) => {
			return {
				currentChannelId: (context.ChatType?.toLowerCase() === "direct" ? context.From ?? context.To : context.To)?.trim() || void 0,
				currentThreadTs: context.ReplyToId,
				hasRepliedRef
			};
		} }
	},
	imessage: {
		id: "imessage",
		capabilities: {
			chatTypes: ["direct", "group"],
			reactions: true,
			media: true
		},
		outbound: { textChunkLimit: 4e3 },
		config: {
			resolveAllowFrom: ({ cfg, accountId }) => (resolveIMessageAccount({
				cfg,
				accountId
			}).config.allowFrom ?? []).map((entry) => String(entry)),
			formatAllowFrom: ({ allowFrom }) => allowFrom.map((entry) => String(entry).trim()).filter(Boolean)
		},
		groups: {
			resolveRequireMention: resolveIMessageGroupRequireMention,
			resolveToolPolicy: resolveIMessageGroupToolPolicy
		},
		threading: { buildToolContext: ({ context, hasRepliedRef }) => {
			return {
				currentChannelId: (context.ChatType?.toLowerCase() === "direct" ? context.From ?? context.To : context.To)?.trim() || void 0,
				currentThreadTs: context.ReplyToId,
				hasRepliedRef
			};
		} }
	}
};
function buildDockFromPlugin(plugin) {
	return {
		id: plugin.id,
		capabilities: plugin.capabilities,
		commands: plugin.commands,
		outbound: plugin.outbound?.textChunkLimit ? { textChunkLimit: plugin.outbound.textChunkLimit } : void 0,
		streaming: plugin.streaming ? { blockStreamingCoalesceDefaults: plugin.streaming.blockStreamingCoalesceDefaults } : void 0,
		elevated: plugin.elevated,
		config: plugin.config ? {
			resolveAllowFrom: plugin.config.resolveAllowFrom,
			formatAllowFrom: plugin.config.formatAllowFrom
		} : void 0,
		groups: plugin.groups,
		mentions: plugin.mentions,
		threading: plugin.threading,
		agentPrompt: plugin.agentPrompt
	};
}
function listPluginDockEntries() {
	const registry = requireActivePluginRegistry();
	const entries = [];
	const seen = /* @__PURE__ */ new Set();
	for (const entry of registry.channels) {
		const plugin = entry.plugin;
		const id = String(plugin.id).trim();
		if (!id || seen.has(id)) continue;
		seen.add(id);
		if (CHAT_CHANNEL_ORDER.includes(plugin.id)) continue;
		const dock = entry.dock ?? buildDockFromPlugin(plugin);
		entries.push({
			id: plugin.id,
			dock,
			order: plugin.meta.order
		});
	}
	return entries;
}
function listChannelDocks() {
	const baseEntries = CHAT_CHANNEL_ORDER.map((id) => ({
		id,
		dock: DOCKS[id],
		order: getChatChannelMeta(id).order
	}));
	const pluginEntries = listPluginDockEntries();
	const combined = [...baseEntries, ...pluginEntries];
	combined.sort((a, b) => {
		const indexA = CHAT_CHANNEL_ORDER.indexOf(a.id);
		const indexB = CHAT_CHANNEL_ORDER.indexOf(b.id);
		const orderA = a.order ?? (indexA === -1 ? 999 : indexA);
		const orderB = b.order ?? (indexB === -1 ? 999 : indexB);
		if (orderA !== orderB) return orderA - orderB;
		return String(a.id).localeCompare(String(b.id));
	});
	return combined.map((entry) => entry.dock);
}
function getChannelDock(id) {
	const core = DOCKS[id];
	if (core) return core;
	const pluginEntry = requireActivePluginRegistry().channels.find((entry) => entry.plugin.id === id);
	if (!pluginEntry) return;
	return pluginEntry.dock ?? buildDockFromPlugin(pluginEntry.plugin);
}

//#endregion
//#region src/config/sessions/metadata.ts
const mergeOrigin = (existing, next) => {
	if (!existing && !next) return;
	const merged = existing ? { ...existing } : {};
	if (next?.label) merged.label = next.label;
	if (next?.provider) merged.provider = next.provider;
	if (next?.surface) merged.surface = next.surface;
	if (next?.chatType) merged.chatType = next.chatType;
	if (next?.from) merged.from = next.from;
	if (next?.to) merged.to = next.to;
	if (next?.accountId) merged.accountId = next.accountId;
	if (next?.threadId != null && next.threadId !== "") merged.threadId = next.threadId;
	return Object.keys(merged).length > 0 ? merged : void 0;
};
function deriveSessionOrigin(ctx) {
	const label = resolveConversationLabel(ctx)?.trim();
	const provider = normalizeMessageChannel(typeof ctx.OriginatingChannel === "string" && ctx.OriginatingChannel || ctx.Surface || ctx.Provider);
	const surface = ctx.Surface?.trim().toLowerCase();
	const chatType = normalizeChatType(ctx.ChatType) ?? void 0;
	const from = ctx.From?.trim();
	const to = (typeof ctx.OriginatingTo === "string" ? ctx.OriginatingTo : ctx.To)?.trim() ?? void 0;
	const accountId = ctx.AccountId?.trim();
	const threadId = ctx.MessageThreadId ?? void 0;
	const origin = {};
	if (label) origin.label = label;
	if (provider) origin.provider = provider;
	if (surface) origin.surface = surface;
	if (chatType) origin.chatType = chatType;
	if (from) origin.from = from;
	if (to) origin.to = to;
	if (accountId) origin.accountId = accountId;
	if (threadId != null && threadId !== "") origin.threadId = threadId;
	return Object.keys(origin).length > 0 ? origin : void 0;
}
function snapshotSessionOrigin(entry) {
	if (!entry?.origin) return;
	return { ...entry.origin };
}
function deriveGroupSessionPatch(params) {
	const resolution = params.groupResolution ?? resolveGroupSessionKey(params.ctx);
	if (!resolution?.channel) return null;
	const channel = resolution.channel;
	const subject = params.ctx.GroupSubject?.trim();
	const space = params.ctx.GroupSpace?.trim();
	const explicitChannel = params.ctx.GroupChannel?.trim();
	const normalizedChannel = normalizeChannelId(channel);
	const isChannelProvider = Boolean(normalizedChannel && getChannelDock(normalizedChannel)?.capabilities.chatTypes.includes("channel"));
	const nextGroupChannel = explicitChannel ?? ((resolution.chatType === "channel" || isChannelProvider) && subject && subject.startsWith("#") ? subject : void 0);
	const nextSubject = nextGroupChannel ? void 0 : subject;
	const patch = {
		chatType: resolution.chatType ?? "group",
		channel,
		groupId: resolution.id
	};
	if (nextSubject) patch.subject = nextSubject;
	if (nextGroupChannel) patch.groupChannel = nextGroupChannel;
	if (space) patch.space = space;
	const displayName = buildGroupDisplayName({
		provider: channel,
		subject: nextSubject ?? params.existing?.subject,
		groupChannel: nextGroupChannel ?? params.existing?.groupChannel,
		space: space ?? params.existing?.space,
		id: resolution.id,
		key: params.sessionKey
	});
	if (displayName) patch.displayName = displayName;
	return patch;
}
function deriveSessionMetaPatch(params) {
	const groupPatch = deriveGroupSessionPatch(params);
	const origin = deriveSessionOrigin(params.ctx);
	if (!groupPatch && !origin) return null;
	const patch = groupPatch ? { ...groupPatch } : {};
	const mergedOrigin = mergeOrigin(params.existing?.origin, origin);
	if (mergedOrigin) patch.origin = mergedOrigin;
	return Object.keys(patch).length > 0 ? patch : null;
}

//#endregion
//#region src/config/sessions/main-session.ts
function resolveMainSessionKey(cfg) {
	if (cfg?.session?.scope === "global") return "global";
	const agents = cfg?.agents?.list ?? [];
	return buildAgentMainSessionKey({
		agentId: normalizeAgentId(agents.find((agent) => agent?.default)?.id ?? agents[0]?.id ?? DEFAULT_AGENT_ID),
		mainKey: normalizeMainKey(cfg?.session?.mainKey)
	});
}
function resolveMainSessionKeyFromConfig() {
	return resolveMainSessionKey(loadConfig());
}
function resolveAgentMainSessionKey(params) {
	const mainKey = normalizeMainKey(params.cfg?.session?.mainKey);
	return buildAgentMainSessionKey({
		agentId: params.agentId,
		mainKey
	});
}
function resolveExplicitAgentSessionKey(params) {
	const agentId = params.agentId?.trim();
	if (!agentId) return;
	return resolveAgentMainSessionKey({
		cfg: params.cfg,
		agentId
	});
}
function canonicalizeMainSessionAlias(params) {
	const raw = params.sessionKey.trim();
	if (!raw) return raw;
	const agentId = normalizeAgentId(params.agentId);
	const mainKey = normalizeMainKey(params.cfg?.session?.mainKey);
	const agentMainSessionKey = buildAgentMainSessionKey({
		agentId,
		mainKey
	});
	const agentMainAliasKey = buildAgentMainSessionKey({
		agentId,
		mainKey: "main"
	});
	const isMainAlias = raw === "main" || raw === mainKey || raw === agentMainSessionKey || raw === agentMainAliasKey;
	if (params.cfg?.session?.scope === "global" && isMainAlias) return "global";
	if (isMainAlias) return agentMainSessionKey;
	return raw;
}

//#endregion
//#region src/config/sessions/types.ts
function mergeSessionEntry(existing, patch) {
	const sessionId = patch.sessionId ?? existing?.sessionId ?? crypto.randomUUID();
	const updatedAt = Math.max(existing?.updatedAt ?? 0, patch.updatedAt ?? 0, Date.now());
	if (!existing) return {
		...patch,
		sessionId,
		updatedAt
	};
	return {
		...existing,
		...patch,
		sessionId,
		updatedAt
	};
}
function resolveFreshSessionTotalTokens(entry) {
	const total = entry?.totalTokens;
	if (typeof total !== "number" || !Number.isFinite(total) || total < 0) return;
	if (entry?.totalTokensFresh === false) return;
	return total;
}
const DEFAULT_RESET_TRIGGERS = ["/new", "/reset"];
const DEFAULT_IDLE_MINUTES = 60;

//#endregion
//#region src/config/sessions/reset.ts
const DEFAULT_RESET_MODE = "daily";
const DEFAULT_RESET_AT_HOUR = 4;
const THREAD_SESSION_MARKERS = [":thread:", ":topic:"];
const GROUP_SESSION_MARKERS = [":group:", ":channel:"];
function isThreadSessionKey(sessionKey) {
	const normalized = (sessionKey ?? "").toLowerCase();
	if (!normalized) return false;
	return THREAD_SESSION_MARKERS.some((marker) => normalized.includes(marker));
}
function resolveSessionResetType(params) {
	if (params.isThread || isThreadSessionKey(params.sessionKey)) return "thread";
	if (params.isGroup) return "group";
	const normalized = (params.sessionKey ?? "").toLowerCase();
	if (GROUP_SESSION_MARKERS.some((marker) => normalized.includes(marker))) return "group";
	return "direct";
}
function resolveThreadFlag(params) {
	if (params.messageThreadId != null) return true;
	if (params.threadLabel?.trim()) return true;
	if (params.threadStarterBody?.trim()) return true;
	if (params.parentSessionKey?.trim()) return true;
	return isThreadSessionKey(params.sessionKey);
}
function resolveDailyResetAtMs(now, atHour) {
	const normalizedAtHour = normalizeResetAtHour(atHour);
	const resetAt = new Date(now);
	resetAt.setHours(normalizedAtHour, 0, 0, 0);
	if (now < resetAt.getTime()) resetAt.setDate(resetAt.getDate() - 1);
	return resetAt.getTime();
}
function resolveSessionResetPolicy(params) {
	const sessionCfg = params.sessionCfg;
	const baseReset = params.resetOverride ?? sessionCfg?.reset;
	const typeReset = params.resetOverride ? void 0 : sessionCfg?.resetByType?.[params.resetType] ?? (params.resetType === "direct" ? (sessionCfg?.resetByType)?.dm : void 0);
	const hasExplicitReset = Boolean(baseReset || sessionCfg?.resetByType);
	const legacyIdleMinutes = params.resetOverride ? void 0 : sessionCfg?.idleMinutes;
	const mode = typeReset?.mode ?? baseReset?.mode ?? (!hasExplicitReset && legacyIdleMinutes != null ? "idle" : DEFAULT_RESET_MODE);
	const atHour = normalizeResetAtHour(typeReset?.atHour ?? baseReset?.atHour ?? DEFAULT_RESET_AT_HOUR);
	const idleMinutesRaw = typeReset?.idleMinutes ?? baseReset?.idleMinutes ?? legacyIdleMinutes;
	let idleMinutes;
	if (idleMinutesRaw != null) {
		const normalized = Math.floor(idleMinutesRaw);
		if (Number.isFinite(normalized)) idleMinutes = Math.max(normalized, 1);
	} else if (mode === "idle") idleMinutes = DEFAULT_IDLE_MINUTES;
	return {
		mode,
		atHour,
		idleMinutes
	};
}
function resolveChannelResetConfig(params) {
	const resetByChannel = params.sessionCfg?.resetByChannel;
	if (!resetByChannel) return;
	const normalized = normalizeMessageChannel(params.channel);
	const fallback = params.channel?.trim().toLowerCase();
	const key = normalized ?? fallback;
	if (!key) return;
	return resetByChannel[key] ?? resetByChannel[key.toLowerCase()];
}
function evaluateSessionFreshness(params) {
	const dailyResetAt = params.policy.mode === "daily" ? resolveDailyResetAtMs(params.now, params.policy.atHour) : void 0;
	const idleExpiresAt = params.policy.idleMinutes != null ? params.updatedAt + params.policy.idleMinutes * 6e4 : void 0;
	const staleDaily = dailyResetAt != null && params.updatedAt < dailyResetAt;
	const staleIdle = idleExpiresAt != null && params.now > idleExpiresAt;
	return {
		fresh: !(staleDaily || staleIdle),
		dailyResetAt,
		idleExpiresAt
	};
}
function normalizeResetAtHour(value) {
	if (typeof value !== "number" || !Number.isFinite(value)) return DEFAULT_RESET_AT_HOUR;
	const normalized = Math.floor(value);
	if (!Number.isFinite(normalized)) return DEFAULT_RESET_AT_HOUR;
	if (normalized < 0) return 0;
	if (normalized > 23) return 23;
	return normalized;
}

//#endregion
//#region src/config/sessions/session-key.ts
function deriveSessionKey(scope, ctx) {
	if (scope === "global") return "global";
	const resolvedGroup = resolveGroupSessionKey(ctx);
	if (resolvedGroup) return resolvedGroup.key;
	return (ctx.From ? normalizeE164(ctx.From) : "") || "unknown";
}
/**
* Resolve the session key with a canonical direct-chat bucket (default: "main").
* All non-group direct chats collapse to this bucket; groups stay isolated.
*/
function resolveSessionKey(scope, ctx, mainKey) {
	const explicit = ctx.SessionKey?.trim();
	if (explicit) return explicit.toLowerCase();
	const raw = deriveSessionKey(scope, ctx);
	if (scope === "global") return raw;
	const canonical = buildAgentMainSessionKey({
		agentId: DEFAULT_AGENT_ID,
		mainKey: normalizeMainKey(mainKey)
	});
	if (!(raw.includes(":group:") || raw.includes(":channel:"))) return canonical;
	return `agent:${DEFAULT_AGENT_ID}:${raw}`;
}

//#endregion
//#region src/agents/session-write-lock.ts
const CLEANUP_SIGNALS = [
	"SIGINT",
	"SIGTERM",
	"SIGQUIT",
	"SIGABRT"
];
const CLEANUP_STATE_KEY = Symbol.for("openclaw.sessionWriteLockCleanupState");
const HELD_LOCKS_KEY = Symbol.for("openclaw.sessionWriteLockHeldLocks");
function resolveHeldLocks() {
	const proc = process;
	if (!proc[HELD_LOCKS_KEY]) proc[HELD_LOCKS_KEY] = /* @__PURE__ */ new Map();
	return proc[HELD_LOCKS_KEY];
}
const HELD_LOCKS = resolveHeldLocks();
function resolveCleanupState() {
	const proc = process;
	if (!proc[CLEANUP_STATE_KEY]) proc[CLEANUP_STATE_KEY] = {
		registered: false,
		cleanupHandlers: /* @__PURE__ */ new Map()
	};
	return proc[CLEANUP_STATE_KEY];
}
function isAlive(pid) {
	if (!Number.isFinite(pid) || pid <= 0) return false;
	try {
		process.kill(pid, 0);
		return true;
	} catch {
		return false;
	}
}
/**
* Synchronously release all held locks.
* Used during process exit when async operations aren't reliable.
*/
function releaseAllLocksSync() {
	for (const [sessionFile, held] of HELD_LOCKS) {
		try {
			if (typeof held.handle.close === "function") held.handle.close().catch(() => {});
		} catch {}
		try {
			fs.rmSync(held.lockPath, { force: true });
		} catch {}
		HELD_LOCKS.delete(sessionFile);
	}
}
function handleTerminationSignal(signal) {
	releaseAllLocksSync();
	const cleanupState = resolveCleanupState();
	if (process.listenerCount(signal) === 1) {
		const handler = cleanupState.cleanupHandlers.get(signal);
		if (handler) {
			process.off(signal, handler);
			cleanupState.cleanupHandlers.delete(signal);
		}
		try {
			process.kill(process.pid, signal);
		} catch {}
	}
}
function registerCleanupHandlers() {
	const cleanupState = resolveCleanupState();
	if (!cleanupState.registered) {
		cleanupState.registered = true;
		process.on("exit", () => {
			releaseAllLocksSync();
		});
	}
	for (const signal of CLEANUP_SIGNALS) {
		if (cleanupState.cleanupHandlers.has(signal)) continue;
		try {
			const handler = () => handleTerminationSignal(signal);
			cleanupState.cleanupHandlers.set(signal, handler);
			process.on(signal, handler);
		} catch {}
	}
}
async function readLockPayload(lockPath) {
	try {
		const raw = await fs$1.readFile(lockPath, "utf8");
		const parsed = JSON.parse(raw);
		if (typeof parsed.pid !== "number") return null;
		if (typeof parsed.createdAt !== "string") return null;
		return {
			pid: parsed.pid,
			createdAt: parsed.createdAt
		};
	} catch {
		return null;
	}
}
async function acquireSessionWriteLock(params) {
	registerCleanupHandlers();
	const timeoutMs = params.timeoutMs ?? 1e4;
	const staleMs = params.staleMs ?? 1800 * 1e3;
	const sessionFile = path.resolve(params.sessionFile);
	const sessionDir = path.dirname(sessionFile);
	await fs$1.mkdir(sessionDir, { recursive: true });
	let normalizedDir = sessionDir;
	try {
		normalizedDir = await fs$1.realpath(sessionDir);
	} catch {}
	const normalizedSessionFile = path.join(normalizedDir, path.basename(sessionFile));
	const lockPath = `${normalizedSessionFile}.lock`;
	const held = HELD_LOCKS.get(normalizedSessionFile);
	if (held) {
		held.count += 1;
		return { release: async () => {
			const current = HELD_LOCKS.get(normalizedSessionFile);
			if (!current) return;
			current.count -= 1;
			if (current.count > 0) return;
			HELD_LOCKS.delete(normalizedSessionFile);
			await current.handle.close();
			await fs$1.rm(current.lockPath, { force: true });
		} };
	}
	const startedAt = Date.now();
	let attempt = 0;
	while (Date.now() - startedAt < timeoutMs) {
		attempt += 1;
		try {
			const handle = await fs$1.open(lockPath, "wx");
			await handle.writeFile(JSON.stringify({
				pid: process.pid,
				createdAt: (/* @__PURE__ */ new Date()).toISOString()
			}, null, 2), "utf8");
			HELD_LOCKS.set(normalizedSessionFile, {
				count: 1,
				handle,
				lockPath
			});
			return { release: async () => {
				const current = HELD_LOCKS.get(normalizedSessionFile);
				if (!current) return;
				current.count -= 1;
				if (current.count > 0) return;
				HELD_LOCKS.delete(normalizedSessionFile);
				await current.handle.close();
				await fs$1.rm(current.lockPath, { force: true });
			} };
		} catch (err) {
			if (err.code !== "EEXIST") throw err;
			const payload = await readLockPayload(lockPath);
			const createdAt = payload?.createdAt ? Date.parse(payload.createdAt) : NaN;
			const stale = !Number.isFinite(createdAt) || Date.now() - createdAt > staleMs;
			const alive = payload?.pid ? isAlive(payload.pid) : false;
			if (stale || !alive) {
				await fs$1.rm(lockPath, { force: true });
				continue;
			}
			const delay = Math.min(1e3, 50 * attempt);
			await new Promise((r) => setTimeout(r, delay));
		}
	}
	const payload = await readLockPayload(lockPath);
	const owner = payload?.pid ? `pid=${payload.pid}` : "unknown";
	throw new Error(`session file locked (timeout ${timeoutMs}ms): ${owner} ${lockPath}`);
}
const __testing = {
	cleanupSignals: [...CLEANUP_SIGNALS],
	handleTerminationSignal,
	releaseAllLocksSync
};

//#endregion
//#region src/utils/account-id.ts
function normalizeAccountId(value) {
	if (typeof value !== "string") return;
	return value.trim() || void 0;
}

//#endregion
//#region src/utils/delivery-context.ts
function normalizeDeliveryContext(context) {
	if (!context) return;
	const channel = typeof context.channel === "string" ? normalizeMessageChannel(context.channel) ?? context.channel.trim() : void 0;
	const to = typeof context.to === "string" ? context.to.trim() : void 0;
	const accountId = normalizeAccountId(context.accountId);
	const threadId = typeof context.threadId === "number" && Number.isFinite(context.threadId) ? Math.trunc(context.threadId) : typeof context.threadId === "string" ? context.threadId.trim() : void 0;
	const normalizedThreadId = typeof threadId === "string" ? threadId ? threadId : void 0 : threadId;
	if (!channel && !to && !accountId && normalizedThreadId == null) return;
	const normalized = {
		channel: channel || void 0,
		to: to || void 0,
		accountId
	};
	if (normalizedThreadId != null) normalized.threadId = normalizedThreadId;
	return normalized;
}
function normalizeSessionDeliveryFields(source) {
	if (!source) return {
		deliveryContext: void 0,
		lastChannel: void 0,
		lastTo: void 0,
		lastAccountId: void 0,
		lastThreadId: void 0
	};
	const merged = mergeDeliveryContext(normalizeDeliveryContext({
		channel: source.lastChannel ?? source.channel,
		to: source.lastTo,
		accountId: source.lastAccountId,
		threadId: source.lastThreadId
	}), normalizeDeliveryContext(source.deliveryContext));
	if (!merged) return {
		deliveryContext: void 0,
		lastChannel: void 0,
		lastTo: void 0,
		lastAccountId: void 0,
		lastThreadId: void 0
	};
	return {
		deliveryContext: merged,
		lastChannel: merged.channel,
		lastTo: merged.to,
		lastAccountId: merged.accountId,
		lastThreadId: merged.threadId
	};
}
function deliveryContextFromSession(entry) {
	if (!entry) return;
	return normalizeSessionDeliveryFields({
		channel: entry.channel,
		lastChannel: entry.lastChannel,
		lastTo: entry.lastTo,
		lastAccountId: entry.lastAccountId,
		lastThreadId: entry.lastThreadId ?? entry.deliveryContext?.threadId ?? entry.origin?.threadId,
		deliveryContext: entry.deliveryContext
	}).deliveryContext;
}
function mergeDeliveryContext(primary, fallback) {
	const normalizedPrimary = normalizeDeliveryContext(primary);
	const normalizedFallback = normalizeDeliveryContext(fallback);
	if (!normalizedPrimary && !normalizedFallback) return;
	return normalizeDeliveryContext({
		channel: normalizedPrimary?.channel ?? normalizedFallback?.channel,
		to: normalizedPrimary?.to ?? normalizedFallback?.to,
		accountId: normalizedPrimary?.accountId ?? normalizedFallback?.accountId,
		threadId: normalizedPrimary?.threadId ?? normalizedFallback?.threadId
	});
}
function deliveryContextKey(context) {
	const normalized = normalizeDeliveryContext(context);
	if (!normalized?.channel || !normalized?.to) return;
	const threadId = normalized.threadId != null && normalized.threadId !== "" ? String(normalized.threadId) : "";
	return `${normalized.channel}|${normalized.to}|${normalized.accountId ?? ""}|${threadId}`;
}

//#endregion
//#region src/config/cache-utils.ts
function resolveCacheTtlMs(params) {
	const { envValue, defaultTtlMs } = params;
	if (envValue) {
		const parsed = Number.parseInt(envValue, 10);
		if (Number.isFinite(parsed) && parsed >= 0) return parsed;
	}
	return defaultTtlMs;
}
function isCacheEnabled(ttlMs) {
	return ttlMs > 0;
}
function getFileMtimeMs(filePath) {
	try {
		return fs.statSync(filePath).mtimeMs;
	} catch {
		return;
	}
}

//#endregion
//#region src/config/sessions/store.ts
const log = createSubsystemLogger("sessions/store");
const SESSION_STORE_CACHE = /* @__PURE__ */ new Map();
const DEFAULT_SESSION_STORE_TTL_MS = 45e3;
function isSessionStoreRecord(value) {
	return !!value && typeof value === "object" && !Array.isArray(value);
}
function getSessionStoreTtl() {
	return resolveCacheTtlMs({
		envValue: process.env.OPENCLAW_SESSION_CACHE_TTL_MS,
		defaultTtlMs: DEFAULT_SESSION_STORE_TTL_MS
	});
}
function isSessionStoreCacheEnabled() {
	return isCacheEnabled(getSessionStoreTtl());
}
function isSessionStoreCacheValid(entry) {
	const now = Date.now();
	const ttl = getSessionStoreTtl();
	return now - entry.loadedAt <= ttl;
}
function invalidateSessionStoreCache(storePath) {
	SESSION_STORE_CACHE.delete(storePath);
}
function normalizeSessionEntryDelivery(entry) {
	const normalized = normalizeSessionDeliveryFields({
		channel: entry.channel,
		lastChannel: entry.lastChannel,
		lastTo: entry.lastTo,
		lastAccountId: entry.lastAccountId,
		lastThreadId: entry.lastThreadId ?? entry.deliveryContext?.threadId ?? entry.origin?.threadId,
		deliveryContext: entry.deliveryContext
	});
	const nextDelivery = normalized.deliveryContext;
	const sameDelivery = (entry.deliveryContext?.channel ?? void 0) === nextDelivery?.channel && (entry.deliveryContext?.to ?? void 0) === nextDelivery?.to && (entry.deliveryContext?.accountId ?? void 0) === nextDelivery?.accountId && (entry.deliveryContext?.threadId ?? void 0) === nextDelivery?.threadId;
	const sameLast = entry.lastChannel === normalized.lastChannel && entry.lastTo === normalized.lastTo && entry.lastAccountId === normalized.lastAccountId && entry.lastThreadId === normalized.lastThreadId;
	if (sameDelivery && sameLast) return entry;
	return {
		...entry,
		deliveryContext: nextDelivery,
		lastChannel: normalized.lastChannel,
		lastTo: normalized.lastTo,
		lastAccountId: normalized.lastAccountId,
		lastThreadId: normalized.lastThreadId
	};
}
function removeThreadFromDeliveryContext(context) {
	if (!context || context.threadId == null) return context;
	const next = { ...context };
	delete next.threadId;
	return next;
}
function normalizeSessionStore(store) {
	for (const [key, entry] of Object.entries(store)) {
		if (!entry) continue;
		const normalized = normalizeSessionEntryDelivery(entry);
		if (normalized !== entry) store[key] = normalized;
	}
}
function loadSessionStore(storePath, opts = {}) {
	if (!opts.skipCache && isSessionStoreCacheEnabled()) {
		const cached = SESSION_STORE_CACHE.get(storePath);
		if (cached && isSessionStoreCacheValid(cached)) {
			if (getFileMtimeMs(storePath) === cached.mtimeMs) return structuredClone(cached.store);
			invalidateSessionStoreCache(storePath);
		}
	}
	let store = {};
	let mtimeMs = getFileMtimeMs(storePath);
	try {
		const raw = fs.readFileSync(storePath, "utf-8");
		const parsed = JSON.parse(raw);
		if (isSessionStoreRecord(parsed)) store = parsed;
		mtimeMs = getFileMtimeMs(storePath) ?? mtimeMs;
	} catch {}
	for (const entry of Object.values(store)) {
		if (!entry || typeof entry !== "object") continue;
		const rec = entry;
		if (typeof rec.channel !== "string" && typeof rec.provider === "string") {
			rec.channel = rec.provider;
			delete rec.provider;
		}
		if (typeof rec.lastChannel !== "string" && typeof rec.lastProvider === "string") {
			rec.lastChannel = rec.lastProvider;
			delete rec.lastProvider;
		}
		if (typeof rec.groupChannel !== "string" && typeof rec.room === "string") {
			rec.groupChannel = rec.room;
			delete rec.room;
		} else if ("room" in rec) delete rec.room;
	}
	if (!opts.skipCache && isSessionStoreCacheEnabled()) SESSION_STORE_CACHE.set(storePath, {
		store: structuredClone(store),
		loadedAt: Date.now(),
		storePath,
		mtimeMs
	});
	return structuredClone(store);
}
function readSessionUpdatedAt(params) {
	try {
		return loadSessionStore(params.storePath)[params.sessionKey]?.updatedAt;
	} catch {
		return;
	}
}
const DEFAULT_SESSION_PRUNE_AFTER_MS = 720 * 60 * 60 * 1e3;
const DEFAULT_SESSION_MAX_ENTRIES = 500;
const DEFAULT_SESSION_ROTATE_BYTES = 10485760;
const DEFAULT_SESSION_MAINTENANCE_MODE = "warn";
function resolvePruneAfterMs(maintenance) {
	const raw = maintenance?.pruneAfter ?? maintenance?.pruneDays;
	if (raw === void 0 || raw === null || raw === "") return DEFAULT_SESSION_PRUNE_AFTER_MS;
	try {
		return parseDurationMs(String(raw).trim(), { defaultUnit: "d" });
	} catch {
		return DEFAULT_SESSION_PRUNE_AFTER_MS;
	}
}
function resolveRotateBytes(maintenance) {
	const raw = maintenance?.rotateBytes;
	if (raw === void 0 || raw === null || raw === "") return DEFAULT_SESSION_ROTATE_BYTES;
	try {
		return parseByteSize(String(raw).trim(), { defaultUnit: "b" });
	} catch {
		return DEFAULT_SESSION_ROTATE_BYTES;
	}
}
/**
* Resolve maintenance settings from openclaw.json (`session.maintenance`).
* Falls back to built-in defaults when config is missing or unset.
*/
function resolveMaintenanceConfig() {
	let maintenance;
	try {
		maintenance = loadConfig().session?.maintenance;
	} catch {}
	return {
		mode: maintenance?.mode ?? DEFAULT_SESSION_MAINTENANCE_MODE,
		pruneAfterMs: resolvePruneAfterMs(maintenance),
		maxEntries: maintenance?.maxEntries ?? DEFAULT_SESSION_MAX_ENTRIES,
		rotateBytes: resolveRotateBytes(maintenance)
	};
}
/**
* Remove entries whose `updatedAt` is older than the configured threshold.
* Entries without `updatedAt` are kept (cannot determine staleness).
* Mutates `store` in-place.
*/
function pruneStaleEntries(store, overrideMaxAgeMs, opts = {}) {
	const maxAgeMs = overrideMaxAgeMs ?? resolveMaintenanceConfig().pruneAfterMs;
	const cutoffMs = Date.now() - maxAgeMs;
	let pruned = 0;
	for (const [key, entry] of Object.entries(store)) if (entry?.updatedAt != null && entry.updatedAt < cutoffMs) {
		delete store[key];
		pruned++;
	}
	if (pruned > 0 && opts.log !== false) log.info("pruned stale session entries", {
		pruned,
		maxAgeMs
	});
	return pruned;
}
/**
* Cap the store to the N most recently updated entries.
* Entries without `updatedAt` are sorted last (removed first when over limit).
* Mutates `store` in-place.
*/
function getEntryUpdatedAt(entry) {
	return entry?.updatedAt ?? Number.NEGATIVE_INFINITY;
}
function getActiveSessionMaintenanceWarning(params) {
	const activeSessionKey = params.activeSessionKey.trim();
	if (!activeSessionKey) return null;
	const activeEntry = params.store[activeSessionKey];
	if (!activeEntry) return null;
	const cutoffMs = (params.nowMs ?? Date.now()) - params.pruneAfterMs;
	const wouldPrune = activeEntry.updatedAt != null ? activeEntry.updatedAt < cutoffMs : false;
	const keys = Object.keys(params.store);
	const wouldCap = keys.length > params.maxEntries && keys.toSorted((a, b) => getEntryUpdatedAt(params.store[b]) - getEntryUpdatedAt(params.store[a])).slice(params.maxEntries).includes(activeSessionKey);
	if (!wouldPrune && !wouldCap) return null;
	return {
		activeSessionKey,
		activeUpdatedAt: activeEntry.updatedAt,
		totalEntries: keys.length,
		pruneAfterMs: params.pruneAfterMs,
		maxEntries: params.maxEntries,
		wouldPrune,
		wouldCap
	};
}
function capEntryCount(store, overrideMax, opts = {}) {
	const maxEntries = overrideMax ?? resolveMaintenanceConfig().maxEntries;
	const keys = Object.keys(store);
	if (keys.length <= maxEntries) return 0;
	const toRemove = keys.toSorted((a, b) => {
		const aTime = getEntryUpdatedAt(store[a]);
		return getEntryUpdatedAt(store[b]) - aTime;
	}).slice(maxEntries);
	for (const key of toRemove) delete store[key];
	if (opts.log !== false) log.info("capped session entry count", {
		removed: toRemove.length,
		maxEntries
	});
	return toRemove.length;
}
async function getSessionFileSize(storePath) {
	try {
		return (await fs.promises.stat(storePath)).size;
	} catch {
		return null;
	}
}
/**
* Rotate the sessions file if it exceeds the configured size threshold.
* Renames the current file to `sessions.json.bak.{timestamp}` and cleans up
* old rotation backups, keeping only the 3 most recent `.bak.*` files.
*/
async function rotateSessionFile(storePath, overrideBytes) {
	const maxBytes = overrideBytes ?? resolveMaintenanceConfig().rotateBytes;
	const fileSize = await getSessionFileSize(storePath);
	if (fileSize == null) return false;
	if (fileSize <= maxBytes) return false;
	const backupPath = `${storePath}.bak.${Date.now()}`;
	try {
		await fs.promises.rename(storePath, backupPath);
		log.info("rotated session store file", {
			backupPath: path.basename(backupPath),
			sizeBytes: fileSize
		});
	} catch {
		return false;
	}
	try {
		const dir = path.dirname(storePath);
		const baseName = path.basename(storePath);
		const backups = (await fs.promises.readdir(dir)).filter((f) => f.startsWith(`${baseName}.bak.`)).toSorted().toReversed();
		const maxBackups = 3;
		if (backups.length > maxBackups) {
			const toDelete = backups.slice(maxBackups);
			for (const old of toDelete) await fs.promises.unlink(path.join(dir, old)).catch(() => void 0);
			log.info("cleaned up old session store backups", { deleted: toDelete.length });
		}
	} catch {}
	return true;
}
async function saveSessionStoreUnlocked(storePath, store, opts) {
	invalidateSessionStoreCache(storePath);
	normalizeSessionStore(store);
	if (!opts?.skipMaintenance) {
		const maintenance = resolveMaintenanceConfig();
		if (maintenance.mode === "warn") {
			const activeSessionKey = opts?.activeSessionKey?.trim();
			if (activeSessionKey) {
				const warning = getActiveSessionMaintenanceWarning({
					store,
					activeSessionKey,
					pruneAfterMs: maintenance.pruneAfterMs,
					maxEntries: maintenance.maxEntries
				});
				if (warning) {
					log.warn("session maintenance would evict active session; skipping enforcement", {
						activeSessionKey: warning.activeSessionKey,
						wouldPrune: warning.wouldPrune,
						wouldCap: warning.wouldCap,
						pruneAfterMs: warning.pruneAfterMs,
						maxEntries: warning.maxEntries
					});
					await opts?.onWarn?.(warning);
				}
			}
		} else {
			pruneStaleEntries(store, maintenance.pruneAfterMs);
			capEntryCount(store, maintenance.maxEntries);
			await rotateSessionFile(storePath, maintenance.rotateBytes);
		}
	}
	await fs.promises.mkdir(path.dirname(storePath), { recursive: true });
	const json = JSON.stringify(store, null, 2);
	if (process.platform === "win32") {
		try {
			await fs.promises.writeFile(storePath, json, "utf-8");
		} catch (err) {
			if ((err && typeof err === "object" && "code" in err ? String(err.code) : null) === "ENOENT") return;
			throw err;
		}
		return;
	}
	const tmp = `${storePath}.${process.pid}.${crypto.randomUUID()}.tmp`;
	try {
		await fs.promises.writeFile(tmp, json, {
			mode: 384,
			encoding: "utf-8"
		});
		await fs.promises.rename(tmp, storePath);
		await fs.promises.chmod(storePath, 384);
	} catch (err) {
		if ((err && typeof err === "object" && "code" in err ? String(err.code) : null) === "ENOENT") {
			try {
				await fs.promises.mkdir(path.dirname(storePath), { recursive: true });
				await fs.promises.writeFile(storePath, json, {
					mode: 384,
					encoding: "utf-8"
				});
				await fs.promises.chmod(storePath, 384);
			} catch (err2) {
				if ((err2 && typeof err2 === "object" && "code" in err2 ? String(err2.code) : null) === "ENOENT") return;
				throw err2;
			}
			return;
		}
		throw err;
	} finally {
		await fs.promises.rm(tmp, { force: true });
	}
}
async function saveSessionStore(storePath, store, opts) {
	await withSessionStoreLock(storePath, async () => {
		await saveSessionStoreUnlocked(storePath, store, opts);
	});
}
async function updateSessionStore(storePath, mutator, opts) {
	return await withSessionStoreLock(storePath, async () => {
		const store = loadSessionStore(storePath, { skipCache: true });
		const result = await mutator(store);
		await saveSessionStoreUnlocked(storePath, store, opts);
		return result;
	});
}
const LOCK_QUEUES = /* @__PURE__ */ new Map();
function lockTimeoutError(storePath) {
	return /* @__PURE__ */ new Error(`timeout waiting for session store lock: ${storePath}`);
}
function getOrCreateLockQueue(storePath) {
	const existing = LOCK_QUEUES.get(storePath);
	if (existing) return existing;
	const created = {
		running: false,
		pending: []
	};
	LOCK_QUEUES.set(storePath, created);
	return created;
}
function removePendingTask(queue, task) {
	const idx = queue.pending.indexOf(task);
	if (idx >= 0) queue.pending.splice(idx, 1);
}
async function drainSessionStoreLockQueue(storePath) {
	const queue = LOCK_QUEUES.get(storePath);
	if (!queue || queue.running) return;
	queue.running = true;
	try {
		while (queue.pending.length > 0) {
			const task = queue.pending.shift();
			if (!task || task.timedOut) continue;
			if (task.timer) clearTimeout(task.timer);
			task.started = true;
			const remainingTimeoutMs = task.timeoutAt != null ? Math.max(0, task.timeoutAt - Date.now()) : Number.POSITIVE_INFINITY;
			if (task.timeoutAt != null && remainingTimeoutMs <= 0) {
				task.timedOut = true;
				task.reject(lockTimeoutError(storePath));
				continue;
			}
			let lock;
			let result;
			let failed;
			let hasFailure = false;
			try {
				lock = await acquireSessionWriteLock({
					sessionFile: storePath,
					timeoutMs: remainingTimeoutMs,
					staleMs: task.staleMs
				});
				result = await task.fn();
			} catch (err) {
				hasFailure = true;
				failed = err;
			} finally {
				await lock?.release().catch(() => void 0);
			}
			if (hasFailure) {
				task.reject(failed);
				continue;
			}
			task.resolve(result);
		}
	} finally {
		queue.running = false;
		if (queue.pending.length === 0) LOCK_QUEUES.delete(storePath);
		else queueMicrotask(() => {
			drainSessionStoreLockQueue(storePath);
		});
	}
}
async function withSessionStoreLock(storePath, fn, opts = {}) {
	const timeoutMs = opts.timeoutMs ?? 1e4;
	const staleMs = opts.staleMs ?? 3e4;
	opts.pollIntervalMs;
	const hasTimeout = timeoutMs > 0 && Number.isFinite(timeoutMs);
	const timeoutAt = hasTimeout ? Date.now() + timeoutMs : void 0;
	const queue = getOrCreateLockQueue(storePath);
	return await new Promise((resolve, reject) => {
		const task = {
			fn: async () => await fn(),
			resolve: (value) => resolve(value),
			reject,
			timeoutAt,
			staleMs,
			started: false,
			timedOut: false
		};
		if (hasTimeout) task.timer = setTimeout(() => {
			if (task.started || task.timedOut) return;
			task.timedOut = true;
			removePendingTask(queue, task);
			reject(lockTimeoutError(storePath));
		}, timeoutMs);
		queue.pending.push(task);
		drainSessionStoreLockQueue(storePath);
	});
}
async function updateSessionStoreEntry(params) {
	const { storePath, sessionKey, update } = params;
	return await withSessionStoreLock(storePath, async () => {
		const store = loadSessionStore(storePath);
		const existing = store[sessionKey];
		if (!existing) return null;
		const patch = await update(existing);
		if (!patch) return existing;
		const next = mergeSessionEntry(existing, patch);
		store[sessionKey] = next;
		await saveSessionStoreUnlocked(storePath, store, { activeSessionKey: sessionKey });
		return next;
	});
}
async function recordSessionMetaFromInbound(params) {
	const { storePath, sessionKey, ctx } = params;
	const createIfMissing = params.createIfMissing ?? true;
	return await updateSessionStore(storePath, (store) => {
		const existing = store[sessionKey];
		const patch = deriveSessionMetaPatch({
			ctx,
			sessionKey,
			existing,
			groupResolution: params.groupResolution
		});
		if (!patch) return existing ?? null;
		if (!existing && !createIfMissing) return null;
		const next = mergeSessionEntry(existing, patch);
		store[sessionKey] = next;
		return next;
	}, { activeSessionKey: sessionKey });
}
async function updateLastRoute(params) {
	const { storePath, sessionKey, channel, to, accountId, threadId, ctx } = params;
	return await withSessionStoreLock(storePath, async () => {
		const store = loadSessionStore(storePath);
		const existing = store[sessionKey];
		const now = Date.now();
		const explicitContext = normalizeDeliveryContext(params.deliveryContext);
		const inlineContext = normalizeDeliveryContext({
			channel,
			to,
			accountId,
			threadId
		});
		const mergedInput = mergeDeliveryContext(explicitContext, inlineContext);
		const explicitDeliveryContext = params.deliveryContext;
		const explicitThreadValue = (explicitDeliveryContext != null && Object.prototype.hasOwnProperty.call(explicitDeliveryContext, "threadId") ? explicitDeliveryContext.threadId : void 0) ?? (threadId != null && threadId !== "" ? threadId : void 0);
		const merged = mergeDeliveryContext(mergedInput, Boolean(explicitContext?.channel || explicitContext?.to || inlineContext?.channel || inlineContext?.to) && explicitThreadValue == null ? removeThreadFromDeliveryContext(deliveryContextFromSession(existing)) : deliveryContextFromSession(existing));
		const normalized = normalizeSessionDeliveryFields({ deliveryContext: {
			channel: merged?.channel,
			to: merged?.to,
			accountId: merged?.accountId,
			threadId: merged?.threadId
		} });
		const metaPatch = ctx ? deriveSessionMetaPatch({
			ctx,
			sessionKey,
			existing,
			groupResolution: params.groupResolution
		}) : null;
		const basePatch = {
			updatedAt: Math.max(existing?.updatedAt ?? 0, now),
			deliveryContext: normalized.deliveryContext,
			lastChannel: normalized.lastChannel,
			lastTo: normalized.lastTo,
			lastAccountId: normalized.lastAccountId,
			lastThreadId: normalized.lastThreadId
		};
		const next = mergeSessionEntry(existing, metaPatch ? {
			...basePatch,
			...metaPatch
		} : basePatch);
		store[sessionKey] = next;
		await saveSessionStoreUnlocked(storePath, store, { activeSessionKey: sessionKey });
		return next;
	});
}

//#endregion
//#region src/config/sessions/transcript.ts
function stripQuery(value) {
	const noHash = value.split("#")[0] ?? value;
	return noHash.split("?")[0] ?? noHash;
}
function extractFileNameFromMediaUrl(value) {
	const trimmed = value.trim();
	if (!trimmed) return null;
	const cleaned = stripQuery(trimmed);
	try {
		const parsed = new URL(cleaned);
		const base = path.basename(parsed.pathname);
		if (!base) return null;
		try {
			return decodeURIComponent(base);
		} catch {
			return base;
		}
	} catch {
		const base = path.basename(cleaned);
		if (!base || base === "/" || base === ".") return null;
		return base;
	}
}
function resolveMirroredTranscriptText(params) {
	const mediaUrls = params.mediaUrls?.filter((url) => url && url.trim()) ?? [];
	if (mediaUrls.length > 0) {
		const names = mediaUrls.map((url) => extractFileNameFromMediaUrl(url)).filter((name) => Boolean(name && name.trim()));
		if (names.length > 0) return names.join(", ");
		return "media";
	}
	const trimmed = (params.text ?? "").trim();
	return trimmed ? trimmed : null;
}
async function ensureSessionHeader(params) {
	if (fs.existsSync(params.sessionFile)) return;
	await fs.promises.mkdir(path.dirname(params.sessionFile), { recursive: true });
	const header = {
		type: "session",
		version: CURRENT_SESSION_VERSION,
		id: params.sessionId,
		timestamp: (/* @__PURE__ */ new Date()).toISOString(),
		cwd: process.cwd()
	};
	await fs.promises.writeFile(params.sessionFile, `${JSON.stringify(header)}\n`, "utf-8");
}
async function appendAssistantMessageToSessionTranscript(params) {
	const sessionKey = params.sessionKey.trim();
	if (!sessionKey) return {
		ok: false,
		reason: "missing sessionKey"
	};
	const mirrorText = resolveMirroredTranscriptText({
		text: params.text,
		mediaUrls: params.mediaUrls
	});
	if (!mirrorText) return {
		ok: false,
		reason: "empty text"
	};
	const storePath = params.storePath ?? resolveDefaultSessionStorePath(params.agentId);
	const entry = loadSessionStore(storePath, { skipCache: true })[sessionKey];
	if (!entry?.sessionId) return {
		ok: false,
		reason: `unknown sessionKey: ${sessionKey}`
	};
	let sessionFile;
	try {
		sessionFile = resolveSessionFilePath(entry.sessionId, entry, { sessionsDir: path.dirname(storePath) });
	} catch (err) {
		return {
			ok: false,
			reason: err instanceof Error ? err.message : String(err)
		};
	}
	await ensureSessionHeader({
		sessionFile,
		sessionId: entry.sessionId
	});
	SessionManager.open(sessionFile).appendMessage({
		role: "assistant",
		content: [{
			type: "text",
			text: mirrorText
		}],
		api: "openai-responses",
		provider: "openclaw",
		model: "delivery-mirror",
		usage: {
			input: 0,
			output: 0,
			cacheRead: 0,
			cacheWrite: 0,
			totalTokens: 0,
			cost: {
				input: 0,
				output: 0,
				cacheRead: 0,
				cacheWrite: 0,
				total: 0
			}
		},
		stopReason: "stop",
		timestamp: Date.now()
	});
	if (!entry.sessionFile || entry.sessionFile !== sessionFile) await updateSessionStore(storePath, (current) => {
		current[sessionKey] = {
			...entry,
			sessionFile
		};
	}, { activeSessionKey: sessionKey });
	emitSessionTranscriptUpdate(sessionFile);
	return {
		ok: true,
		sessionFile
	};
}

//#endregion
//#region src/agents/sandbox/runtime-status.ts
function shouldSandboxSession(cfg, sessionKey, mainSessionKey) {
	if (cfg.mode === "off") return false;
	if (cfg.mode === "all") return true;
	return sessionKey.trim() !== mainSessionKey.trim();
}
function resolveMainSessionKeyForSandbox(params) {
	if (params.cfg?.session?.scope === "global") return "global";
	return resolveAgentMainSessionKey({
		cfg: params.cfg,
		agentId: params.agentId
	});
}
function resolveComparableSessionKeyForSandbox(params) {
	return canonicalizeMainSessionAlias({
		cfg: params.cfg,
		agentId: params.agentId,
		sessionKey: params.sessionKey
	});
}
function resolveSandboxRuntimeStatus(params) {
	const sessionKey = params.sessionKey?.trim() ?? "";
	const agentId = resolveSessionAgentId({
		sessionKey,
		config: params.cfg
	});
	const cfg = params.cfg;
	const sandboxCfg = resolveSandboxConfigForAgent(cfg, agentId);
	const mainSessionKey = resolveMainSessionKeyForSandbox({
		cfg,
		agentId
	});
	const sandboxed = sessionKey ? shouldSandboxSession(sandboxCfg, resolveComparableSessionKeyForSandbox({
		cfg,
		agentId,
		sessionKey
	}), mainSessionKey) : false;
	return {
		agentId,
		sessionKey,
		mainSessionKey,
		mode: sandboxCfg.mode,
		sandboxed,
		toolPolicy: resolveSandboxToolPolicyForAgent(cfg, agentId)
	};
}
function formatSandboxToolPolicyBlockedMessage(params) {
	const tool = params.toolName.trim().toLowerCase();
	if (!tool) return;
	const runtime = resolveSandboxRuntimeStatus({
		cfg: params.cfg,
		sessionKey: params.sessionKey
	});
	if (!runtime.sandboxed) return;
	const deny = new Set(expandToolGroups(runtime.toolPolicy.deny));
	const allow = expandToolGroups(runtime.toolPolicy.allow);
	const allowSet = allow.length > 0 ? new Set(allow) : null;
	const blockedByDeny = deny.has(tool);
	const blockedByAllow = allowSet ? !allowSet.has(tool) : false;
	if (!blockedByDeny && !blockedByAllow) return;
	const reasons = [];
	const fixes = [];
	if (blockedByDeny) {
		reasons.push("deny list");
		fixes.push(`Remove "${tool}" from ${runtime.toolPolicy.sources.deny.key}.`);
	}
	if (blockedByAllow) {
		reasons.push("allow list");
		fixes.push(`Add "${tool}" to ${runtime.toolPolicy.sources.allow.key} (or set it to [] to allow all).`);
	}
	const lines = [];
	lines.push(`Tool "${tool}" blocked by sandbox tool policy (mode=${runtime.mode}).`);
	lines.push(`Session: ${runtime.sessionKey || "(unknown)"}`);
	lines.push(`Reason: ${reasons.join(" + ")}`);
	lines.push("Fix:");
	lines.push(`- agents.defaults.sandbox.mode=off (disable sandbox)`);
	for (const fix of fixes) lines.push(`- ${fix}`);
	if (runtime.mode === "non-main") lines.push(`- Use main session key (direct): ${runtime.mainSessionKey}`);
	lines.push(`- See: ${formatCliCommand(`openclaw sandbox explain --session ${runtime.sessionKey}`)}`);
	return lines.join("\n");
}

//#endregion
//#region src/agents/sandbox/workspace.ts
async function ensureSandboxWorkspace(workspaceDir, seedFrom, skipBootstrap) {
	await fs$1.mkdir(workspaceDir, { recursive: true });
	if (seedFrom) {
		const seed = resolveUserPath(seedFrom);
		const files = [
			DEFAULT_AGENTS_FILENAME,
			DEFAULT_SOUL_FILENAME,
			DEFAULT_TOOLS_FILENAME,
			DEFAULT_IDENTITY_FILENAME,
			DEFAULT_USER_FILENAME,
			DEFAULT_BOOTSTRAP_FILENAME,
			DEFAULT_HEARTBEAT_FILENAME
		];
		for (const name of files) {
			const src = path.join(seed, name);
			const dest = path.join(workspaceDir, name);
			try {
				await fs$1.access(dest);
			} catch {
				try {
					const content = await fs$1.readFile(src, "utf-8");
					await fs$1.writeFile(dest, content, {
						encoding: "utf-8",
						flag: "wx"
					});
				} catch {}
			}
		}
	}
	await ensureAgentWorkspace({
		dir: workspaceDir,
		ensureBootstrapFiles: !skipBootstrap
	});
}

//#endregion
//#region src/agents/sandbox/context.ts
async function resolveSandboxContext(params) {
	const rawSessionKey = params.sessionKey?.trim();
	if (!rawSessionKey) return null;
	const runtime = resolveSandboxRuntimeStatus({
		cfg: params.config,
		sessionKey: rawSessionKey
	});
	if (!runtime.sandboxed) return null;
	const cfg = resolveSandboxConfigForAgent(params.config, runtime.agentId);
	await maybePruneSandboxes(cfg);
	const agentWorkspaceDir = resolveUserPath(params.workspaceDir?.trim() || DEFAULT_AGENT_WORKSPACE_DIR);
	const workspaceRoot = resolveUserPath(cfg.workspaceRoot);
	const scopeKey = resolveSandboxScopeKey(cfg.scope, rawSessionKey);
	const sandboxWorkspaceDir = cfg.scope === "shared" ? workspaceRoot : resolveSandboxWorkspaceDir(workspaceRoot, scopeKey);
	const workspaceDir = cfg.workspaceAccess === "rw" ? agentWorkspaceDir : sandboxWorkspaceDir;
	if (workspaceDir === sandboxWorkspaceDir) {
		await ensureSandboxWorkspace(sandboxWorkspaceDir, agentWorkspaceDir, params.config?.agents?.defaults?.skipBootstrap);
		if (cfg.workspaceAccess !== "rw") try {
			await syncSkillsToWorkspace({
				sourceWorkspaceDir: agentWorkspaceDir,
				targetWorkspaceDir: sandboxWorkspaceDir,
				config: params.config
			});
		} catch (error) {
			const message = error instanceof Error ? error.message : JSON.stringify(error);
			defaultRuntime.error?.(`Sandbox skill sync failed: ${message}`);
		}
	} else await fs$1.mkdir(workspaceDir, { recursive: true });
	const containerName = await ensureSandboxContainer({
		sessionKey: rawSessionKey,
		workspaceDir,
		agentWorkspaceDir,
		cfg
	});
	const browser = await ensureSandboxBrowser({
		scopeKey,
		workspaceDir,
		agentWorkspaceDir,
		cfg,
		evaluateEnabled: params.config?.browser?.evaluateEnabled ?? DEFAULT_BROWSER_EVALUATE_ENABLED
	});
	const sandboxContext = {
		enabled: true,
		sessionKey: rawSessionKey,
		workspaceDir,
		agentWorkspaceDir,
		workspaceAccess: cfg.workspaceAccess,
		containerName,
		containerWorkdir: cfg.docker.workdir,
		docker: cfg.docker,
		tools: cfg.tools,
		browserAllowHostControl: cfg.browser.allowHostControl,
		browser: browser ?? void 0
	};
	sandboxContext.fsBridge = createSandboxFsBridge({ sandbox: sandboxContext });
	return sandboxContext;
}
async function ensureSandboxWorkspaceForSession(params) {
	const rawSessionKey = params.sessionKey?.trim();
	if (!rawSessionKey) return null;
	const runtime = resolveSandboxRuntimeStatus({
		cfg: params.config,
		sessionKey: rawSessionKey
	});
	if (!runtime.sandboxed) return null;
	const cfg = resolveSandboxConfigForAgent(params.config, runtime.agentId);
	const agentWorkspaceDir = resolveUserPath(params.workspaceDir?.trim() || DEFAULT_AGENT_WORKSPACE_DIR);
	const workspaceRoot = resolveUserPath(cfg.workspaceRoot);
	const scopeKey = resolveSandboxScopeKey(cfg.scope, rawSessionKey);
	const sandboxWorkspaceDir = cfg.scope === "shared" ? workspaceRoot : resolveSandboxWorkspaceDir(workspaceRoot, scopeKey);
	const workspaceDir = cfg.workspaceAccess === "rw" ? agentWorkspaceDir : sandboxWorkspaceDir;
	if (workspaceDir === sandboxWorkspaceDir) {
		await ensureSandboxWorkspace(sandboxWorkspaceDir, agentWorkspaceDir, params.config?.agents?.defaults?.skipBootstrap);
		if (cfg.workspaceAccess !== "rw") try {
			await syncSkillsToWorkspace({
				sourceWorkspaceDir: agentWorkspaceDir,
				targetWorkspaceDir: sandboxWorkspaceDir,
				config: params.config
			});
		} catch (error) {
			const message = error instanceof Error ? error.message : JSON.stringify(error);
			defaultRuntime.error?.(`Sandbox skill sync failed: ${message}`);
		}
	} else await fs$1.mkdir(workspaceDir, { recursive: true });
	return {
		workspaceDir,
		containerWorkdir: cfg.docker.workdir
	};
}

//#endregion
//#region src/agents/sandbox/manage.ts
async function listSandboxContainers() {
	const config = loadConfig();
	const registry = await readRegistry();
	const results = [];
	for (const entry of registry.entries) {
		const state = await dockerContainerState(entry.containerName);
		let actualImage = entry.image;
		if (state.exists) try {
			const result = await execDocker([
				"inspect",
				"-f",
				"{{.Config.Image}}",
				entry.containerName
			], { allowFailure: true });
			if (result.code === 0) actualImage = result.stdout.trim();
		} catch {}
		const configuredImage = resolveSandboxConfigForAgent(config, resolveSandboxAgentId(entry.sessionKey)).docker.image;
		results.push({
			...entry,
			image: actualImage,
			running: state.running,
			imageMatch: actualImage === configuredImage
		});
	}
	return results;
}
async function listSandboxBrowsers() {
	const config = loadConfig();
	const registry = await readBrowserRegistry();
	const results = [];
	for (const entry of registry.entries) {
		const state = await dockerContainerState(entry.containerName);
		let actualImage = entry.image;
		if (state.exists) try {
			const result = await execDocker([
				"inspect",
				"-f",
				"{{.Config.Image}}",
				entry.containerName
			], { allowFailure: true });
			if (result.code === 0) actualImage = result.stdout.trim();
		} catch {}
		const configuredImage = resolveSandboxConfigForAgent(config, resolveSandboxAgentId(entry.sessionKey)).browser.image;
		results.push({
			...entry,
			image: actualImage,
			running: state.running,
			imageMatch: actualImage === configuredImage
		});
	}
	return results;
}
async function removeSandboxContainer(containerName) {
	try {
		await execDocker([
			"rm",
			"-f",
			containerName
		], { allowFailure: true });
	} catch {}
	await removeRegistryEntry(containerName);
}
async function removeSandboxBrowserContainer(containerName) {
	try {
		await execDocker([
			"rm",
			"-f",
			containerName
		], { allowFailure: true });
	} catch {}
	await removeBrowserRegistryEntry(containerName);
	for (const [sessionKey, bridge] of BROWSER_BRIDGES.entries()) if (bridge.containerName === containerName) {
		await stopBrowserBridgeServer(bridge.bridge.server).catch(() => void 0);
		BROWSER_BRIDGES.delete(sessionKey);
	}
}

//#endregion
export { resolveSandboxConfigForAgent as $, resolveChannelResetConfig as A, resolveMainSessionKeyFromConfig as B, normalizeDeliveryContext as C, deriveSessionKey as D, acquireSessionWriteLock as E, resolveFreshSessionTotalTokens as F, listEnabledSignalAccounts as G, snapshotSessionOrigin as H, canonicalizeMainSessionAlias as I, resolveChannelGroupPolicy as J, resolveSignalAccount as K, resolveAgentMainSessionKey as L, resolveSessionResetType as M, resolveThreadFlag as N, resolveSessionKey as O, DEFAULT_RESET_TRIGGERS as P, resolveGroupSessionKey as Q, resolveExplicitAgentSessionKey as R, mergeDeliveryContext as S, normalizeAccountId as T, getChannelDock as U, deriveSessionMetaPatch as V, listChannelDocks as W, resolveChannelGroupToolsPolicy as X, resolveChannelGroupRequireMention as Y, buildGroupDisplayName as Z, updateSessionStoreEntry as _, ensureSandboxWorkspaceForSession as a, expandPolicyWithPluginGroups as at, deliveryContextFromSession as b, resolveSandboxRuntimeStatus as c, resolveToolProfilePolicy as ct, loadSessionStore as d, DEFAULT_SANDBOX_COMMON_IMAGE as dt, resolveSandboxScope as et, readSessionUpdatedAt as f, DEFAULT_SANDBOX_IMAGE as ft, updateSessionStore as g, updateLastRoute as h, removeSandboxContainer as i, collectExplicitAllowlist as it, resolveSessionResetPolicy as j, evaluateSessionFreshness as k, appendAssistantMessageToSessionTranscript as l, stripPluginOnlyAllowlist as lt, saveSessionStore as m, listSandboxContainers as n, applyOwnerOnlyToolPolicy as nt, resolveSandboxContext as o, expandToolGroups as ot, recordSessionMetaFromInbound as p, resolveConversationLabel as pt, resolveIMessageAccount as q, removeSandboxBrowserContainer as r, buildPluginToolGroups as rt, formatSandboxToolPolicyBlockedMessage as s, normalizeToolName as st, listSandboxBrowsers as t, resolveSandboxToolPolicyForAgent as tt, resolveMirroredTranscriptText as u, DEFAULT_SANDBOX_BROWSER_IMAGE as ut, isCacheEnabled as v, normalizeSessionDeliveryFields as w, deliveryContextKey as x, resolveCacheTtlMs as y, resolveMainSessionKey as z };
import type { AgentTool } from "@mariozechner/pi-agent-core";
import type { BashSandboxConfig } from "./bash-tools.shared.js";
import { type ExecAsk, type ExecHost, type ExecSecurity } from "../infra/exec-approvals.js";
type PtyExitEvent = {
    exitCode: number;
    signal?: number;
};
type PtyListener<T> = (event: T) => void;
type PtyHandle = {
    pid: number;
    write: (data: string | Buffer) => void;
    onData: (listener: PtyListener<string>) => void;
    onExit: (listener: PtyListener<PtyExitEvent>) => void;
};
type PtySpawn = (file: string, args: string[] | string, options: {
    name?: string;
    cols?: number;
    rows?: number;
    cwd?: string;
    env?: Record<string, string>;
}) => PtyHandle;
type PtyModule = {
    spawn?: PtySpawn;
    default?: {
        spawn?: PtySpawn;
    };
};
type PtyModuleLoader = () => Promise<PtyModule>;
export declare function setPtyModuleLoaderForTests(loader?: PtyModuleLoader): void;
export type ExecToolDefaults = {
    host?: ExecHost;
    security?: ExecSecurity;
    ask?: ExecAsk;
    node?: string;
    pathPrepend?: string[];
    safeBins?: string[];
    agentId?: string;
    backgroundMs?: number;
    timeoutSec?: number;
    approvalRunningNoticeMs?: number;
    sandbox?: BashSandboxConfig;
    elevated?: ExecElevatedDefaults;
    allowBackground?: boolean;
    scopeKey?: string;
    sessionKey?: string;
    messageProvider?: string;
    notifyOnExit?: boolean;
    cwd?: string;
};
export type { BashSandboxConfig } from "./bash-tools.shared.js";
export type ExecElevatedDefaults = {
    enabled: boolean;
    allowed: boolean;
    defaultLevel: "on" | "off" | "ask" | "full";
};
export type ExecToolDetails = {
    status: "running";
    sessionId: string;
    pid?: number;
    startedAt: number;
    cwd?: string;
    tail?: string;
} | {
    status: "completed" | "failed";
    exitCode: number | null;
    durationMs: number;
    aggregated: string;
    cwd?: string;
} | {
    status: "approval-pending";
    approvalId: string;
    approvalSlug: string;
    expiresAtMs: number;
    host: ExecHost;
    command: string;
    cwd?: string;
    nodeId?: string;
};
export declare function createExecTool(defaults?: ExecToolDefaults): AgentTool<any, ExecToolDetails>;
export declare const execTool: AgentTool<any, ExecToolDetails>;

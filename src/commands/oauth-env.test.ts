import { afterEach, describe, expect, it, vi } from "vitest";
import { isRemoteEnvironment } from "./oauth-env.js";

const REMOTE_ENV_KEYS = [
  "OPENCLAW_OAUTH_REMOTE",
  "SSH_CLIENT",
  "SSH_TTY",
  "SSH_CONNECTION",
  "SSH2_CLIENT",
  "VSCODE_AGENT_FOLDER",
  "VSCODE_REMOTE_CONTAINERS_SESSION",
  "VSCODE_CLI_REMOTE_CONNECTION_TOKEN",
  "REMOTE_CONTAINERS",
  "CODESPACES",
  "DISPLAY",
  "WAYLAND_DISPLAY",
  "WSL_INTEROP",
  "WSL_DISTRO_NAME",
  "WSLENV",
] as const;

function resetRemoteEnv() {
  for (const key of REMOTE_ENV_KEYS) {
    vi.stubEnv(key, undefined);
  }
}

describe("isRemoteEnvironment", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("treats OPENCLAW_OAUTH_REMOTE=1 as remote", () => {
    resetRemoteEnv();
    vi.stubEnv("OPENCLAW_OAUTH_REMOTE", "1");

    expect(isRemoteEnvironment()).toBe(true);
  });

  it("treats SSH2_CLIENT as remote", () => {
    resetRemoteEnv();
    vi.stubEnv("SSH2_CLIENT", "10.0.0.1 22 10.0.0.2 12345");

    expect(isRemoteEnvironment()).toBe(true);
  });

  it("treats VS Code remote agent env as remote", () => {
    resetRemoteEnv();
    vi.stubEnv("VSCODE_AGENT_FOLDER", "/home/user/.vscode-server");

    expect(isRemoteEnvironment()).toBe(true);
  });

  it("stays local when no remote markers are set", () => {
    resetRemoteEnv();
    // Keep linux desktops from being treated as headless remote.
    vi.stubEnv("DISPLAY", ":0");
    vi.stubEnv("WAYLAND_DISPLAY", "wayland-0");

    expect(isRemoteEnvironment()).toBe(false);
  });
});

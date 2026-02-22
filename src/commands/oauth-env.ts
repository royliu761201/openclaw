import { isWSLEnv } from "../infra/wsl.js";

function isTruthyFlag(value: string | undefined): boolean {
  if (!value) {
    return false;
  }
  const normalized = value.trim().toLowerCase();
  return normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on";
}

export function isRemoteEnvironment(): boolean {
  // Manual escape hatch for cases where remote shells hide SSH markers.
  if (isTruthyFlag(process.env.OPENCLAW_OAUTH_REMOTE)) {
    return true;
  }

  if (process.env.SSH_CLIENT || process.env.SSH_TTY || process.env.SSH_CONNECTION) {
    return true;
  }

  if (process.env.SSH2_CLIENT) {
    return true;
  }

  // VS Code Remote and similar remotes often do not expose SSH_* vars in spawned shells.
  if (
    process.env.VSCODE_AGENT_FOLDER ||
    process.env.VSCODE_REMOTE_CONTAINERS_SESSION ||
    process.env.VSCODE_CLI_REMOTE_CONNECTION_TOKEN
  ) {
    return true;
  }

  if (process.env.REMOTE_CONTAINERS || process.env.CODESPACES) {
    return true;
  }

  if (
    process.platform === "linux" &&
    !process.env.DISPLAY &&
    !process.env.WAYLAND_DISPLAY &&
    !isWSLEnv()
  ) {
    return true;
  }

  return false;
}

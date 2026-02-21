import type { OpenClawConfig } from "../config/config.js";
import { ensureModelAllowlistEntry } from "./model-allowlist.js";

export const GOOGLE_VERTEX_DEFAULT_MODEL = "google-vertex/gemini-3-pro-preview";

export function applyGoogleVertexProviderConfig(cfg: OpenClawConfig): OpenClawConfig {
  const next = ensureModelAllowlistEntry({
    cfg,
    modelRef: GOOGLE_VERTEX_DEFAULT_MODEL,
  });
  const models = { ...next.agents?.defaults?.models };
  models[GOOGLE_VERTEX_DEFAULT_MODEL] = {
    ...models[GOOGLE_VERTEX_DEFAULT_MODEL],
    alias: models[GOOGLE_VERTEX_DEFAULT_MODEL]?.alias ?? "Gemini Vertex",
  };

  return {
    ...next,
    agents: {
      ...next.agents,
      defaults: {
        ...next.agents?.defaults,
        models,
      },
    },
  };
}

export function applyGoogleVertexConfig(cfg: OpenClawConfig): OpenClawConfig {
  const next = applyGoogleVertexProviderConfig(cfg);
  return {
    ...next,
    agents: {
      ...next.agents,
      defaults: {
        ...next.agents?.defaults,
        model:
          next.agents?.defaults?.model && typeof next.agents.defaults.model === "object"
            ? {
                ...next.agents.defaults.model,
                primary: GOOGLE_VERTEX_DEFAULT_MODEL,
              }
            : { primary: GOOGLE_VERTEX_DEFAULT_MODEL },
      },
    },
  };
}

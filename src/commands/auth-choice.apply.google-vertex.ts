import { resolveEnvApiKey } from "../agents/model-auth.js";
import { formatCliCommand } from "../cli/command-format.js";
import type { ApplyAuthChoiceParams, ApplyAuthChoiceResult } from "./auth-choice.apply.js";
import { applyDefaultModelChoice } from "./auth-choice.default-model.js";
import {
  applyGoogleVertexConfig,
  applyGoogleVertexProviderConfig,
  GOOGLE_VERTEX_DEFAULT_MODEL,
} from "./google-vertex-model-default.js";

export async function applyAuthChoiceGoogleVertex(
  params: ApplyAuthChoiceParams,
): Promise<ApplyAuthChoiceResult | null> {
  if (params.authChoice !== "google-vertex") {
    return null;
  }

  let nextConfig = params.config;
  let agentModelOverride: string | undefined;
  const noteAgentModel = async (model: string) => {
    if (!params.agentId) {
      return;
    }
    await params.prompter.note(
      `Default model set to ${model} for agent "${params.agentId}".`,
      "Model configured",
    );
  };

  const envAuth = resolveEnvApiKey("google-vertex");
  if (!envAuth) {
    await params.prompter.note(
      [
        "Google Vertex requires Application Default Credentials (ADC).",
        `Run ${formatCliCommand("gcloud auth application-default login")}`,
        "Then set GOOGLE_CLOUD_PROJECT (or GCLOUD_PROJECT) and GOOGLE_CLOUD_LOCATION.",
      ].join("\n"),
      "Google Vertex",
    );
    return { config: nextConfig };
  }

  await params.prompter.note(`Vertex auth detected (${envAuth.source}).`, "Google Vertex");

  const applied = await applyDefaultModelChoice({
    config: nextConfig,
    setDefaultModel: params.setDefaultModel,
    defaultModel: GOOGLE_VERTEX_DEFAULT_MODEL,
    applyDefaultConfig: applyGoogleVertexConfig,
    applyProviderConfig: applyGoogleVertexProviderConfig,
    noteDefault: GOOGLE_VERTEX_DEFAULT_MODEL,
    noteAgentModel,
    prompter: params.prompter,
  });
  nextConfig = applied.config;
  agentModelOverride = applied.agentModelOverride ?? agentModelOverride;

  return { config: nextConfig, agentModelOverride };
}

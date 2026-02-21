import { describe, expect, it, vi } from "vitest";
import type { RuntimeEnv } from "../runtime.js";
import type { WizardPrompter } from "../wizard/prompts.js";

const resolveEnvApiKey = vi.hoisted(() => vi.fn());

vi.mock("../agents/model-auth.js", () => ({
  resolveEnvApiKey,
}));

import { applyAuthChoiceGoogleVertex } from "./auth-choice.apply.google-vertex.js";
import { GOOGLE_VERTEX_DEFAULT_MODEL } from "./google-vertex-model-default.js";

function makePrompter(): WizardPrompter {
  return {
    intro: async () => {},
    outro: async () => {},
    note: async () => {},
    select: async () => "",
    multiselect: async () => [],
    text: async () => "",
    confirm: async () => false,
    progress: () => ({ update: () => {}, stop: () => {} }),
  };
}

function makeRuntime(): RuntimeEnv {
  return {
    log: () => {},
    error: () => {},
    exit: () => {
      throw new Error("exit");
    },
  };
}

describe("applyAuthChoiceGoogleVertex", () => {
  it("returns null for other auth choices", async () => {
    const result = await applyAuthChoiceGoogleVertex({
      authChoice: "gemini-api-key",
      config: {},
      prompter: makePrompter(),
      runtime: makeRuntime(),
      setDefaultModel: true,
    });
    expect(result).toBeNull();
  });

  it("keeps config unchanged when vertex auth is missing", async () => {
    resolveEnvApiKey.mockReturnValueOnce(null);
    const note = vi.fn(async () => {});
    const prompter = {
      ...makePrompter(),
      note,
    };

    const result = await applyAuthChoiceGoogleVertex({
      authChoice: "google-vertex",
      config: {},
      prompter,
      runtime: makeRuntime(),
      setDefaultModel: true,
    });

    expect(result).toEqual({ config: {} });
    expect(note).toHaveBeenCalled();
  });

  it("sets default model when vertex auth exists", async () => {
    resolveEnvApiKey.mockReturnValueOnce({
      apiKey: "<authenticated>",
      source: "gcloud adc",
    });

    const result = await applyAuthChoiceGoogleVertex({
      authChoice: "google-vertex",
      config: {},
      prompter: makePrompter(),
      runtime: makeRuntime(),
      setDefaultModel: true,
    });

    expect(result?.config.agents?.defaults?.model).toEqual({
      primary: GOOGLE_VERTEX_DEFAULT_MODEL,
    });
  });

  it("returns agent override when setDefaultModel is false", async () => {
    resolveEnvApiKey.mockReturnValueOnce({
      apiKey: "<authenticated>",
      source: "gcloud adc",
    });

    const result = await applyAuthChoiceGoogleVertex({
      authChoice: "google-vertex",
      config: {},
      prompter: makePrompter(),
      runtime: makeRuntime(),
      setDefaultModel: false,
      agentId: "alpha",
    });

    expect(result?.agentModelOverride).toBe(GOOGLE_VERTEX_DEFAULT_MODEL);
    expect(result?.config.agents?.defaults?.models?.[GOOGLE_VERTEX_DEFAULT_MODEL]).toEqual({
      alias: "Gemini Vertex",
    });
  });
});

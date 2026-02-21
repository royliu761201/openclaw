import { describe, expect, it } from "vitest";
import { isModernModelRef } from "./live-model-filter.js";

describe("isModernModelRef", () => {
  it("treats google family providers as modern for gemini-3 models", () => {
    expect(isModernModelRef({ provider: "google", id: "gemini-3-pro-preview" })).toBe(true);
    expect(isModernModelRef({ provider: "google-gemini-cli", id: "gemini-3-pro-preview" })).toBe(
      true,
    );
    expect(isModernModelRef({ provider: "google-vertex", id: "gemini-3-pro-preview" })).toBe(true);
  });

  it("keeps antigravity special handling for claude aliases", () => {
    expect(
      isModernModelRef({ provider: "google-antigravity", id: "claude-opus-4-6-thinking" }),
    ).toBe(true);
    expect(isModernModelRef({ provider: "google-antigravity", id: "legacy-model" })).toBe(false);
  });
});

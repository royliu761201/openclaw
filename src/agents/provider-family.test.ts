import { describe, expect, it } from "vitest";
import {
  isGoogleModelApi,
  isGoogleProvider,
  requiresGoogleToolSchemaSanitization,
} from "./provider-family.js";

describe("provider family helpers", () => {
  it("identifies Google providers", () => {
    expect(isGoogleProvider("google")).toBe(true);
    expect(isGoogleProvider("google-antigravity")).toBe(true);
    expect(isGoogleProvider("google-gemini-cli")).toBe(true);
    expect(isGoogleProvider("google-vertex")).toBe(true);
    expect(isGoogleProvider("openai")).toBe(false);
  });

  it("identifies Google model APIs", () => {
    expect(isGoogleModelApi("google-generative-ai")).toBe(true);
    expect(isGoogleModelApi("google-antigravity")).toBe(true);
    expect(isGoogleModelApi("google-gemini-cli")).toBe(true);
    expect(isGoogleModelApi("google-vertex")).toBe(true);
    expect(isGoogleModelApi("openai-responses")).toBe(false);
  });

  it("applies Google schema sanitization policy to Google family providers", () => {
    expect(requiresGoogleToolSchemaSanitization("google")).toBe(true);
    expect(requiresGoogleToolSchemaSanitization("google-vertex")).toBe(true);
    expect(requiresGoogleToolSchemaSanitization("openai")).toBe(false);
  });
});

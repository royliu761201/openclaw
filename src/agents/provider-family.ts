import { normalizeProviderId } from "./model-selection.js";

const GOOGLE_PROVIDER_IDS = new Set([
  "google",
  "google-antigravity",
  "google-gemini-cli",
  "google-vertex",
]);

const GOOGLE_MODEL_API_IDS = new Set([
  "google-generative-ai",
  "google-antigravity",
  "google-gemini-cli",
  "google-vertex",
]);

export function isGoogleProvider(provider?: string | null): boolean {
  if (!provider) {
    return false;
  }
  return GOOGLE_PROVIDER_IDS.has(normalizeProviderId(provider));
}

export function isGoogleModelApi(modelApi?: string | null): boolean {
  if (!modelApi) {
    return false;
  }
  return GOOGLE_MODEL_API_IDS.has(modelApi.trim().toLowerCase());
}

export function requiresGoogleToolSchemaSanitization(provider?: string | null): boolean {
  return isGoogleProvider(provider);
}

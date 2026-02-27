import { resolveEnvApiKey } from "./src/agents/model-auth.js";
import { loadDotEnv } from "./src/infra/dotenv.js";

loadDotEnv(process.cwd()); // Explicitly pass cwd
console.log("process.env.GEMINI_API_KEY:", process.env.GEMINI_API_KEY ? "EXISTS" : "UNDEFINED");
console.log("resolveEnvApiKey('google'):", resolveEnvApiKey("google"));

#!/usr/bin/env node
import { Stagehand, ModelProvider } from "@browserbasehq/stagehand";
import { z } from "zod";
import fs from "fs";
import path from "path";

// Simple argument parser
const args = process.argv.slice(2);
const command = args[0];
const params = args.slice(1);

// Configuration
const SCREENSHOTS_DIR = path.join(process.cwd(), "agent", "browser_screenshots");
const DOWNLOADS_DIR = path.join(process.cwd(), "agent", "downloads");

// Ensure directories exist
fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
fs.mkdirSync(DOWNLOADS_DIR, { recursive: true });

async function main() {
  if (!command) {
    console.error("No command specified");
    process.exit(1);
  }

  // Load environment variables from ~/.openclaw/.env if available
  const homeDir = process.env.HOME || process.env.USERPROFILE || "";
  const envPath = path.join(homeDir, ".openclaw", ".env");
  
  if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, "utf-8");
      envContent.split(/\r?\n/).forEach(line => {
          const match = line.match(/^([^=]+)=(.*)$/);
          if (match) {
              const key = match[1].trim();
              const value = match[2].trim().replace(/^["']|["']$/g, ""); // Remove quotes
              if (!process.env[key]) {
                  process.env[key] = value;
              }
          }
      });
  }

  // Load configuration from ~/.openclaw/openclaw.json
  const configPath = path.join(homeDir, ".openclaw", "openclaw.json");
  let provider = "google"; // Default fallback
  let modelName = "gemini-2.0-flash";

  if (fs.existsSync(configPath)) {
      try {
          const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
          const primaryModel = config?.agents?.defaults?.model?.primary;
          if (primaryModel) {
              const parts = primaryModel.split("/");
              if (parts.length === 2) {
                  provider = parts[0];
                  modelName = parts[1];
              } else {
                  modelName = primaryModel;
                  // Guess provider if not prefixed
                  if (modelName.startsWith("ppt") || modelName.startsWith("gpt")) provider = "openai";
                  else if (modelName.startsWith("claude")) provider = "anthropic";
                  else if (modelName.includes("gemini")) provider = "google";
              }
          }
      } catch (e) {
          // Ignore error, use defaults
      }
  }

  // Stagehand Model Fallbacks (Model 2.5 is not yet fully supported in this version of Stagehand)
  if (modelName === "gemini-2.5-flash-lite") {
      modelName = "gemini-2.0-flash-lite"; 
  }

  // Map provider to API Key
  let apiKey = "";
  if (provider === "google") provider = "google"; // Stagehand uses 'google'
  
  if (provider === "google") apiKey = process.env.GEMINI_API_KEY || "";
  else if (provider === "anthropic") apiKey = process.env.ANTHROPIC_API_KEY || "";
  else if (provider === "openai") apiKey = process.env.OPENAI_API_KEY || "";

  if (!apiKey) {
     console.error(JSON.stringify({ 
       success: false, 
       error: `Missing API Key for provider '${provider}'. Please check your ~/.openclaw/.env file.` 
     }, null, 2));
     process.exit(1);
  }

  const modelConfig = {
      provider: provider as any,
      modelName: modelName,
      apiKey: apiKey
  };

    // Initialize Stagehand
    const stagehand = new Stagehand({
      env: "LOCAL",
      verbose: 1,
      headless: true,
      model: modelConfig
    } as any);
  
    try {
        await stagehand.init();
        
        let output: any = { success: true };
    
        switch (command) {
          case "navigate": {
            const url = params[0];
            if (!url) throw new Error("URL is required");
            await stagehand.act(`Navigate to ${url}`);
            output.message = `Successfully navigated to ${url}`;
            break;
          }
            
          case "act": {
            const action = params[0];
            if (!action) throw new Error("Action description is required");
            await stagehand.act(action);
            output.message = `Successfully performed action: ${action}`;
            break;
          }
      
          case "extract": {
            const instruction = params[0];
            const schemaStr = params[1];
            if (!instruction || !schemaStr) throw new Error("Instruction and schema are required");
            


            let schemaJson: any;
            try {
                schemaJson = JSON.parse(schemaStr);
            } catch (e) {
                // Try simplified syntax: key:type,key2:type2
                if (schemaStr.includes(':')) {
                    schemaJson = {};
                    schemaStr.split(',').forEach((pair: string) => {
                        const [key, type] = pair.split(':').map((s: string) => s.trim());
                        if (key && type) {
                            schemaJson[key] = type;
                        }
                    });
                } else {
                     throw new Error("Invalid schema format. Must be JSON or key:type pairs.");
                }
            }

            const zodShape: any = {};
            
            for (const key in schemaJson) {
               const type = schemaJson[key];
               if (type === 'number') zodShape[key] = z.number();
               else if (type === 'boolean') zodShape[key] = z.boolean();
               else zodShape[key] = z.string();
            }
      
            const data = await stagehand.extract(
             instruction,
             z.object(zodShape)
            );
            output.data = data;
            break;
          }
      
          case "observe": {
            const query = params[0];
             if (!query) throw new Error("Observation query is required");
            const elements = await stagehand.observe(query);
            output.data = elements;
            break;
          }
      
          case "screenshot": {
             throw new Error("Screenshot not implemented for V3 CLI yet");
          }
            
          case "close": {
            await stagehand.close();
            output.message = "Browser closed";
            break;
          }
      
          default:
            throw new Error(`Unknown command: ${command}`);
        }
      
        // Always output JSON
        console.log(JSON.stringify(output, null, 2));
      
      } catch (error: any) {
    console.error(JSON.stringify({ 
      success: false, 
      error: error.message 
    }, null, 2));
    process.exit(1);
  } finally {
      if (command === 'close') {
          await stagehand.close();
      } else {
          await stagehand.close();
      }
  }
}
  
main();

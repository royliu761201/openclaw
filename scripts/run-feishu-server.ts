
import * as Lark from "@larksuiteoapi/node-sdk";
import { monitorFeishuProvider } from "../extensions/feishu/src/monitor";

async function main() {
    console.log("Starting Feishu Webhook Server for testing...");

    const mockCfg = {
        commands: {
            useAccessGroups: false
        },
        messages: {
            groupChat: {
                historyLimit: 10
            }
        }
    } as any;

    // We need to export monitorSingleAccount but it is not exported. 
    // However monitorFeishuProvider calls monitorSingleAccount internally if we pass account ID.
    // And to make monitorSingleAccount work, we need an account that resolves.

    // Actually, monitorFeishuProvider uses resolveFeishuAccount which reads from config/env.
    // We can't easily inject a mock account into monitorFeishuProvider without mocking resolveFeishuAccount.

    // Let's create a minimal server manually using the exported registerEventHandlers, like the previous test, 
    // but this time actually start an HTTP server.

    const http = await import("http");
    const { registerEventHandlers } = await import("../extensions/feishu/src/monitor");

    const port = 3000;
    const path = "/feishu/events";
    const eventDispatcher = new Lark.EventDispatcher({});

    // Register our handlers (which will do the logging we want to verify)
    registerEventHandlers(eventDispatcher, {
        cfg: mockCfg,
        accountId: "test-webhook-account",
        runtime: {
            log: (...args: any[]) => console.log("[WebhookLog]", ...args),
            error: (...args: any[]) => console.error("[WebhookError]", ...args),
        } as any,
        chatHistories: new Map(),
        fireAndForget: true, // webhook mode
    });

    const server = http.createServer();
    const webhookHandler = Lark.adaptDefault(path, eventDispatcher, { autoChallenge: true });

    server.on("request", (req, res) => {
        // Simple body accumulation
        let body = "";
        req.on("data", chunk => body += chunk);
        req.on("end", () => {
            // We'll trust the adaptDefault to handle logic, but we need to pass a req that has the body 
            // if adaptDefault expects it. Lark SDK usually handles this.
            // Actually adaptDefault takes (req, res) and might parse body itself if not consumed?
            // Let's just pass it through.

            // Note: adaptDefault might expect "body" property on req if using a framework like express,
            // but for raw node http, it usually consumes the stream.
            // Let's try passing directly first.

            webhookHandler(req, res);
        });
    });

    server.listen(port, () => {
        console.log(`Test Webhook Server listening on http://localhost:${port}${path}`);
    });
}

main().catch(console.error);

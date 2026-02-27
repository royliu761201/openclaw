
import * as Lark from "@larksuiteoapi/node-sdk";
import { registerEventHandlers } from "../extensions/feishu/src/monitor";

async function main() {
    console.log("Starting Feishu News Test...");

    const handlers_registry: Record<string, (data: any) => Promise<void>> = {};

    const mockDispatcherShim = {
        register: (handlers: any) => {
            Object.assign(handlers_registry, handlers);
        }
    } as unknown as Lark.EventDispatcher;

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

    registerEventHandlers(mockDispatcherShim, {
        cfg: mockCfg,
        accountId: "test-account",
        runtime: {
            log: (...args: any[]) => console.log("[RuntimeLog]", ...args),
            error: (...args: any[]) => console.error("[RuntimeError]", ...args),
        } as any,
        chatHistories: new Map(),
        fireAndForget: false, // await handling
    });

    console.log("Handlers registered. Simulating 'News' event (Post type)...");

    // Mock a "News" event.
    const newsEvent = {
        message: {
            message_id: "msg_123",
            chat_id: "chat_123",
            chat_type: "group",
            message_type: "post",
            content: JSON.stringify({
                title: "Breaking News",
                content: [
                    [
                        { tag: "text", text: "Something happened in Feishu!" },
                        { tag: "a", text: "Read more", href: "http://example.com" }
                    ]
                ]
            }),
            mentions: []
        },
        sender: {
            sender_id: {
                open_id: "ou_sender123",
                user_id: "user_sender123"
            }
        }
    };

    if (handlers_registry["im.message.receive_v1"]) {
        // We expect this to fail or log errors because we didn't mock everything (like API clients),
        // but we SHOULD see our "raw event received" log first.
        try {
            await handlers_registry["im.message.receive_v1"](newsEvent);
        } catch (e) {
            console.log("Handler threw error (expected due to missing mocks):", e);
        }
        console.log("Event processed step complete.");
    } else {
        console.error("Handler for im.message.receive_v1 not registered!");
    }

    console.log("\nSimulating 'Interactive' card (potential news source)...");
    const interactiveEvent = {
        message: {
            message_id: "msg_456",
            chat_id: "chat_123",
            chat_type: "group",
            message_type: "interactive",
            content: JSON.stringify({
                header: { title: { content: "News Card", tag: "plain_text" } },
                elements: [{ tag: "div", text: { content: "Some news content", tag: "plain_text" } }]
            }),
            mentions: []
        },
        sender: {
            sender_id: {
                open_id: "ou_sender123",
                user_id: "user_sender123"
            }
        }
    };

    if (handlers_registry["im.message.receive_v1"]) {
        try {
            await handlers_registry["im.message.receive_v1"](interactiveEvent);
        } catch (e) {
            console.log("Handler threw error (expected):", e);
        }
    }

}

main().catch(console.error);

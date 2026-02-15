#!/usr/bin/env node

// 简单的 Tavily API 测试脚本
const TAVILY_API_KEY = process.env.TAVILY_API_KEY;
const TAVILY_API_ENDPOINT = "https://api.tavily.com/search";

async function testTavilySearch() {
  console.log("Testing Tavily API...");
  console.log(`API Key: ${TAVILY_API_KEY ? TAVILY_API_KEY.substring(0, 8) + "..." : "NOT SET"}`);

  if (!TAVILY_API_KEY) {
    console.error("❌ TAVILY_API_KEY environment variable not set");
    process.exit(1);
  }

  try {
    const response = await fetch(TAVILY_API_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        api_key: TAVILY_API_KEY,
        query: "latest AI news",
        max_results: 3,
        include_answer: true,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`❌ API Error (${response.status}): ${errorText}`);
      process.exit(1);
    }

    const data = await response.json();
    console.log("\n✅ Tavily API 调用成功!\n");

    console.log("📊 Results:");
    if (data.results && data.results.length > 0) {
      data.results.forEach((result, index) => {
        console.log(`\n${index + 1}. ${result.title || "No title"}`);
        console.log(`   URL: ${result.url || "No URL"}`);
        console.log(
          `   Content: ${result.content ? result.content.substring(0, 100) + "..." : "No content"}`,
        );
      });
    } else {
      console.log("No results found");
    }

    if (data.answer) {
      console.log("\n💡 AI Answer:");
      console.log(data.answer);
    }

    console.log("\n✅ 测试完成！Tavily 集成正常工作。");
  } catch (error) {
    console.error("❌ Test failed:", error.message);
    process.exit(1);
  }
}

testTavilySearch();

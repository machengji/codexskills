// 视觉识别 CLI（vision-analyze 技能用）
// 用法: node vision-cli.mjs <图片路径或URL> [提示词]
// 配置: 读取 E:\machengji\vision-mcp\.env（VISION_API_BASE_URL / VISION_API_PATH / VISION_API_KEY / VISION_MODEL / VISION_TIMEOUT_MS / VISION_MAX_TOKENS）
// 输出: 识别结果文字（stdout），失败时退出码非 0
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ENV_CANDIDATES = [
  "E:\\machengji\\vision-mcp\\.env",
  path.join(__dirname, ".env"),
];

function loadEnv(file) {
  const env = {};
  try {
    for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
      if (m && !m[1].startsWith("#")) env[m[1]] = m[2].trim();
    }
  } catch {}
  return env;
}

const env = {};
for (const f of ENV_CANDIDATES) {
  if (fs.existsSync(f)) Object.assign(env, loadEnv(f));
}

const MIME = {
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".bmp": "image/bmp", ".gif": "image/gif", ".webp": "image/webp",
  ".tif": "image/tiff", ".tiff": "image/tiff",
};

function isUrl(s) {
  return /^https?:\/\//i.test(s);
}

async function toImageUrl(input) {
  if (isUrl(input)) return input;
  const abs = path.resolve(input);
  if (!fs.existsSync(abs)) throw new Error("图片不存在: " + abs);
  const ext = path.extname(abs).toLowerCase();
  const mime = MIME[ext] || "image/png";
  const b64 = fs.readFileSync(abs).toString("base64");
  return "data:" + mime + ";base64," + b64;
}

async function main() {
  const image = process.argv[2];
  const prompt = process.argv[3] || "请详细描述这张图片的内容，并提取图中所有文字。";
  if (!image) {
    console.error("用法: node vision-cli.mjs <图片路径或URL> [提示词]");
    process.exit(1);
  }
  const base = (env.VISION_API_BASE_URL || "https://ollama.com").replace(/\/+$/, "");
  const apiPath = env.VISION_API_PATH || "/v1/chat/completions";
  const key = env.VISION_API_KEY || "";
  const model = env.VISION_MODEL || "gemma4:31b";
  const maxTokens = Number(env.VISION_MAX_TOKENS || 4096);
  const timeoutMs = Number(env.VISION_TIMEOUT_MS || 60000);
  if (!key || key.includes("REPLACE_ME")) {
    console.error("VISION_API_KEY 未配置，请检查 E:\\machengji\\vision-mcp\\.env");
    process.exit(1);
  }
  const url = new URL(apiPath, base + "/").toString();
  const imageUrl = await toImageUrl(image);
  const body = {
    model,
    max_tokens: maxTokens,
    messages: [{
      role: "user",
      content: [
        { type: "text", text: prompt },
        { type: "image_url", image_url: { url: imageUrl } },
      ],
    }],
  };
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  let res;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key,
      },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
  } catch (e) {
    clearTimeout(timer);
    console.error("请求失败: " + (e.name === "AbortError" ? "超时(" + timeoutMs + "ms)" : e.message));
    process.exit(1);
  }
  clearTimeout(timer);
  const text = await res.text();
  if (!res.ok) {
    console.error("上游错误 " + res.status + " " + text.slice(0, 500));
    process.exit(1);
  }
  let data;
  try { data = JSON.parse(text); } catch { console.error("响应不是 JSON: " + text.slice(0, 500)); process.exit(1); }
  const out = (data.choices || []).map((c) => c.message?.content ?? "").join("\n").trim();
  if (!out) {
    console.error("识别结果为空: " + text.slice(0, 500));
    process.exit(1);
  }
  console.log(out);
}

main().catch((e) => { console.error("识别失败: " + (e && e.message ? e.message : String(e))); process.exit(1); });
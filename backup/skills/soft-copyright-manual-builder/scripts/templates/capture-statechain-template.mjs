import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const OUT = "E:\\已完成的案例-可做参考\\_soft_shots\\{{PKG}}";
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

const BASE = "http://127.0.0.1:5211";
const log = [];
const bad = [];

const b = await chromium.launch({ channel: "chrome", headless: true });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1.5 });
p.setDefaultTimeout(25000);
p.on("response", (r) => { if (r.status() >= 400) bad.push(r.status() + " " + r.url()); });
p.on("pageerror", (e) => bad.push("PAGEERR " + String(e).slice(0, 200)));

async function shot(id, group, action, before, after, changes, popup = false) {
  await p.waitForTimeout(450);
  await p.screenshot({ path: path.join(OUT, id + ".jpg"), fullPage: false, type: "jpeg", quality: 92 });
  log.push({ id, group, action, beforeState: before, afterState: after, visibleChanges: changes, popup });
  console.log("SHOT", id);
}
async function btn(name) {
  await p.getByRole("button", { name, exact: true }).first().click({ timeout: 10000 });
}
async function go(pathname, wait = 1500) {
  await p.goto(BASE + pathname, { waitUntil: "domcontentloaded" });
  await p.waitForTimeout(wait);
}
async function login() {
  await go("/", 1700);
  await p.locator("input").nth(0).fill("demo");
  await p.locator('input[type="password"]').fill("demo123");
  await btn("持令入席");
  await p.waitForSelector(".scale-bar", { timeout: 25000 });
  await p.waitForTimeout(1800);
}

// ---------- 组一 登录入席 ----------
await go("/", 1700);
await shot("s01-login-blank", "登录入席", "打开系统首页，未填任何凭据", "未入席", "戗堤断面水位针首页", "双尺刻度、三张中国现场对照图、入席表单与当班闸段快照", false);
await p.locator("input").nth(0).fill("demo");
await p.locator('input[type="password"]').fill("wrong");
await btn("持令入席");
await p.waitForTimeout(1300);
await shot("s02-login-bad", "登录入席", "输入错误闸段令牌后提交", "已填凭据", "提示口令与当班闸段令牌不符", "表单下方出现错误提示行，页面未跳转", false);
await p.locator('input[type="password"]').fill("demo123");
await btn("持令入席");
await p.waitForSelector(".scale-bar", { timeout: 25000 });
await p.waitForTimeout(1800);
await shot("s03-desk-enter", "登录入席", "输入正确令牌后入席", "登录页", "进入截流窗口台", "顶部双尺就位、左闸段签条列出六闸段、导航十一项、底部留痕", false);

// ---------- 组二 截流窗口台（初始锁截流令 → 试算 → 写入 → 签发） ----------
await p.locator(".stage input").nth(0).fill("151.6");
await p.locator(".stage input").nth(1).fill("146.1");
await p.waitForTimeout(700);
await shot("s04-desk-fill-high", "截流窗口台", "把戗堤高程手改为 151.6、预报水位改为 146.1，尚未提交", "输入框为 147.2 与 146.4", "输入框为试算值，判定框仍是旧值", "两个输入框读数变化，右侧超高余量与判定框保持上一状态未重算", false);

await btn("解超高余量并写入");
await p.waitForTimeout(2000);
await shot("s05-desk-solved", "截流窗口台", "点解超高余量并写入提交算高", "余量 -2.300 锁截流令", "余量转正判可截流", "顶部双尺针位移动、Δh 判定框由红转绿、左闸段签色转绿、底部留痕新增写入记录", false);

await btn("签发截流令");
await p.waitForTimeout(2000);
await shot("s06-desk-lock-ok", "截流窗口台", "在可截流闸段上签发截流令", "可截流", "闸段转入已截流", "中央左闸扇由红转绿、闸段签条状态文字变化、留痕新增锁截流令", false);

await btn("填超高不足试算值");
await p.waitForTimeout(500);
await btn("解超高余量并写入");
await p.waitForTimeout(2000);
await shot("s07-desk-low", "截流窗口台", "点填超高不足试算值并写入", "可截流", "回到锁截流令", "戗堤读数降到 146.8、预报升到 147.4、判定框转红、左闸扇回红", false);

await btn("升紧急");
await p.waitForTimeout(2000);
await shot("s08-desk-urgent", "截流窗口台", "点升紧急把汛期剩余压到 8 日以内", "紧急窗口计数 0", "窗口转紧急", "紧急窗口计数由 0 转 1、右闸扇状态文字变化、留痕新增窗口升级", false);

await btn("三方对账");
await p.waitForTimeout(1800);
await shot("s09-desk-tripay", "截流窗口台", "点三方对账重算首单偏差", "计价单对账中", "计价单转锁定", "右侧资格分拆解首单状态列变化、底部留痕新增对账记录", false);

await btn("算资格分");
await p.waitForTimeout(1800);
await shot("s10-desk-score", "截流窗口台", "点算资格分重算首单加权分", "资格分旧值", "资格分新值", "右侧拆解戳 S 值与可出证文字变化、底部留痕新增", false);

await btn("导出窗口作业单");
await p.waitForTimeout(1800);
await shot("s11-desk-export", "截流窗口台", "点导出窗口作业单", "无作业单", "右侧抽屉展开作业单", "抽屉覆盖右上角并列出闸段戗堤与窗口两组数据", true);

await btn("收下");
await p.waitForTimeout(700);
await btn("窗口销号");
await p.waitForTimeout(1800);
await shot("s12-desk-close", "截流窗口台", "点窗口销号关闭当班窗口", "窗口紧急", "窗口已销号", "窗口状态列变化、底部留痕新增销号记录", false);

// ---------- 组三 闸段WBS ----------
await go("/desk/wbs");
await shot("s13-wbs-tree", "闸段WBS", "进入闸段WBS", "截流窗口台", "工序树与仓号表", "左侧工序树列出十一个节点、中央仓号表与仓号明细、右侧开仓条件与工序节点名册", false);

await p.locator(".tree button").nth(8).click();
await p.waitForTimeout(900);
await btn("核算开仓条件");
await p.waitForTimeout(1800);
await shot("s14-wbs-pick", "闸段WBS", "在工序树上点选河床4#开仓节点并核算开仓条件", "选中左岸2#-仓乙", "选中河床4#开仓且给出开仓结论", "左侧节点高亮转移、中央仓号表与明细行高亮、右侧节点状态与开仓许可刷新并给出冷缝判定", false);

await p.locator(".stage input").nth(0).fill("14");
await p.locator(".stage input").nth(1).fill("26");
await btn("核算开仓条件");
await p.waitForTimeout(1800);
await shot("s15-wbs-cond", "闸段WBS", "把间歇小时改为 14、仓面气温改为 26 后核算开仓条件", "未核算", "给出冷缝判定与模板侧压", "右侧出现冷缝动作与侧压数值、开仓许可文字变化、节点名册该行标记变化", false);

await p.locator("table button", { hasText: "开仓" }).nth(5).click();
await p.waitForTimeout(2600);
await shot("s16-wbs-open", "闸段WBS", "在仓号表上点河床4#-仓丁的开仓按钮", "该仓待开仓状态列", "该仓转浇筑中", "该行状态列由待开仓转浇筑中、左侧工序树同节点状态同步、明细表开仓条件列同步、留痕新增开仓", false);

// ---------- 组四 戗堤高程（重置后从锁截流令出发） ----------
await go("/desk/berm");
await shot("s17-berm-table", "戗堤高程", "进入戗堤高程", "闸段WBS", "测点表与超高曲线", "测点表八列、双色超高曲线、判据分档台账、当班测次统计四区", false);

await p.locator(".stage input").nth(0).fill("152.4");
await p.locator(".stage input").nth(1).fill("145.8");
await btn("写入测点并解超高");
await p.waitForTimeout(2000);
await shot("s18-berm-write", "戗堤高程", "把当班闸段戗堤改为 152.4、预报改为 145.8 后写入", "余量 -2.300 锁截流令", "余量转正判可截流", "表格该行判定转可截流、曲线橙线抬升、顶部双尺同步、底部读数带刷新", false);

await btn("锁截流");
await p.waitForTimeout(2800);
await shot("s19-berm-lock", "戗堤高程", "点锁截流签发截流令", "可截流且按钮可用", "已截流且按钮转禁用", "表格该行状态转已截流、顶部双尺下方判定框、锁截流按钮转灰、留痕新增锁截流令", false);

await p.locator("table tbody tr").nth(3).click();
await p.waitForTimeout(1000);
await shot("s20-berm-switch", "戗堤高程", "在测点表上点选河床4#闸段", "当班左岸1#闸段", "切换选中河床4#闸段", "表格高亮行变化、曲线圆点高亮转移、顶部双尺与闸段签条同步、底部读数带换值", false);

// ---------- 组五 仓面浇筑（选河床4#-仓丁，从待开仓出发） ----------
await go("/desk/pour");
await p.locator(".stage select").selectOption("河床4#-仓丁");
await p.waitForTimeout(1200);
await shot("s21-pour-base", "仓面浇筑", "进入仓面浇筑并选河床4#-仓丁", "戗堤高程", "待开仓仓面与温控闸口表", "顶部参数带、左侧强度条该仓为空、中央仓卡片、右侧温控表与强度判据四区", false);

await p.locator(".stage input").nth(0).fill("980");
await p.locator(".stage input").nth(1).fill("8");
await p.locator(".stage input").nth(2).fill("23.5");
await btn("写入报量并解强度");
await p.waitForTimeout(2600);
await shot("s22-pour-report", "仓面浇筑", "把报量改为 980、可用工时 8、峰值温度 23.5 后写入", "该仓待开仓强度 0", "该仓转浇筑中", "左侧强度条该仓由空转满、温控表该仓 Q_8h 与开仓条件变化、仓卡片刷新、顶部提示条出现解算结论", false);

await p.locator(".stage input").nth(2).fill("31.6");
await btn("写入报量并解强度");
await p.waitForTimeout(2600);
await shot("s23-pour-heat", "仓面浇筑", "把峰值温度改为 31.6 后再次写入", "峰值温度 23.5 受控", "转超温并锁下一仓开仓", "温控表该仓超温判定转超温、开仓条件转暂不支持、强度条着色变化、顶部提示条更新结论", false);

await p.locator(".stage input").nth(4).fill("85");
await btn("坍落度闸口");
await p.waitForTimeout(2600);
await shot("s24-pour-slump", "仓面浇筑", "把坍落度改为 85 后点坍落度闸口核验", "仓态浇筑中", "按闸口结论转已锁仓", "温控表该仓状态转已锁仓且开仓条件转暂不支持、左侧强度条该仓转红、顶部提示条给出闸口结论", false);

// ---------- 组六 验工对账 ----------
await go("/desk/tripay");
await shot("s25-tripay-cols", "验工对账", "进入验工对账", "仓面浇筑", "三方立方四列对照与汇总", "左四列列出单号与立方、每列底部合计带、右侧偏差脊与偏差明细表、底部三方对照汇总", false);

await p.locator(".stage select").selectOption("验-右岸6-03");
await p.waitForTimeout(900);
await p.locator(".stage input").nth(0).fill("1180");
await p.locator(".stage input").nth(1).fill("760");
await p.locator(".stage input").nth(2).fill("1020");
await btn("写入三方并解偏差");
await p.waitForTimeout(2600);
await shot("s26-tripay-check", "验工对账", "选验-右岸6-03 并把承包方 1180、监理抽检 760 写入后解偏差", "该单偏差在限内可流转", "偏差超限锁计价单", "四列卡片该单数值与偏差刷新、超限卡片转红边、偏差脊该单转红标锁定、汇总表该行结论由可流转转锁计价单、KPI 超限计数加一", false);

// ---------- 组七 计价锁定 ----------
await go("/desk/pay");
await p.locator(".stage select").selectOption("验-左岸1-04");
await p.waitForTimeout(900);
await shot("s27-pay-cert", "计价锁定", "进入计价锁定并选验-左岸1-04", "验工对账", "低资格分计价单证书", "左侧支付证书显示该单质量闭合率 0.71 与资格分 0.72、核验清单质量项与资格分项标待闭合、名册该行高亮", false);

await p.locator(".stage input").nth(0).fill("0.95");
await p.locator(".stage input").nth(1).fill("0.96");
await btn("重算资格分");
await p.waitForTimeout(2000);
await shot("s28-pay-score", "计价锁定", "把质量闭合率与安全销号率提到 0.95、0.96 后重算资格分", "资格分 0.72 不许出证", "资格分 0.97 可出证", "证书资格分由 0.72 升至 0.97、状态行由对账中转已申报可出证、核验清单质量项与资格分项转通过、右侧戳由红转绿、分档条变化", false);

await btn("签发支付证书");
await p.waitForTimeout(2000);
await shot("s29-pay-issue", "计价锁定", "点签发支付证书", "已申报可出证", "证书已签发", "证书状态行转已签发、名册该单状态列变化、留痕新增签发", false);

await btn("退回计价单");
await p.waitForTimeout(2000);
await shot("s30-pay-return", "计价锁定", "点退回计价单", "已签发", "计价单已退回", "名册该单状态转已退回、证书状态行同步、右侧各单状态列表同步、留痕新增退回", false);

// ---------- 组八 质量验收 ----------
await go("/desk/quality");
await shot("s31-quality-grid", "质量验收", "进入质量验收", "计价锁定", "单元闭合方格", "五个单元方格按闭合状态着色并列出不合格数、与阈值差、区间上下限，右侧闭合表单与工地对照", false);

await p.locator("button.cell").nth(2).click();
await p.waitForTimeout(900);
await p.locator(".stage input").nth(0).fill("16");
await p.locator(".stage input").nth(1).fill("16");
await btn("写入闭合并解Wilson");
await p.waitForTimeout(2000);
await shot("s32-quality-close", "质量验收", "点选一单元并把合格数与样本数都改为 16 后写入闭合", "该单元未闭合", "闭合通过", "方格该单元转已闭合底色、右侧给出 Wilson 区间与销号率、闭合统计 KPI 变化、留痕新增", false);

// ---------- 组九 三维现场 ----------
await go("/desk/twin-site", 3400);
await shot("s33-twin-site", "坝址整场三维", "进入坝址整场三维", "质量验收", "坝址整场场景", "坝段、导流明渠、围堰戗堤、拌合楼、缆机塔、江面齐备，部件名册与相机面板就位", false);
await btn("江面侧视");
await p.waitForTimeout(1700);
await shot("s34-twin-site-cam", "坝址整场三维", "点江面侧视切换相机", "高位总览", "江面侧视", "视角整体变化，坝段与明渠相对位置与遮挡关系改变", false);
await p.locator(".hud.c li").nth(3).click();
await p.waitForTimeout(900);
await btn("按闸口状态着色");
await p.waitForTimeout(1700);
await shot("s35-twin-site-state", "坝址整场三维", "点部件名册第四项并点按闸口状态着色", "未点选", "部件选中且按状态着色", "左上 HUD 选中部件名变化、围堰与坝段按锁仓状态改色", false);

await go("/desk/twin-pour", 3400);
await shot("s36-twin-pour", "浇筑仓近景三维", "进入浇筑仓近景三维", "坝址整场", "浇筑仓近景场景", "仓面模板、冷却水管网格、振捣棒、层升色带齐备，底部胶片带列出仓面构件", false);
await btn("冷却管近景");
await p.waitForTimeout(1700);
await shot("s37-twin-pour-cam", "浇筑仓近景三维", "点冷却管近景切换相机", "仓口俯视", "冷却管近景", "视角拉近到冷却水管网格，模板与振捣棒相对位置改变", false);
await btn("模板内侧");
await p.waitForTimeout(1700);
await p.locator(".film button").nth(14).click();
await p.waitForTimeout(900);
await btn("按锁仓状态改升层色");
await p.waitForTimeout(1700);
await shot("s38-twin-pour-state", "浇筑仓近景三维", "点模板内侧换视角，再点振捣棒构件并按锁仓状态改升层色", "冷却管近景未点选", "模板内侧视角且构件选中改色", "视角由冷却管近景转到模板内侧、右侧选中构件名变化、层升色带按锁仓状态改色", false);

await go("/desk/twin-divert", 3400);
await shot("s39-twin-divert", "导流洞剖面三维", "进入导流洞剖面三维", "浇筑仓近景", "导流洞剖面场景", "洞身衬砌环、闸门槽、水流粒子、监测点齐备，左侧监测点签条就位", false);
await btn("闸门槽近景");
await p.waitForTimeout(1700);
await shot("s40-twin-divert-cam", "导流洞剖面三维", "点闸门槽近景切换相机", "洞口轴测", "闸门槽近景", "视角拉近到闸门槽，衬砌环透视关系改变", false);
await p.locator(".ticks button").nth(2).click();
await p.waitForTimeout(900);
await btn("闸门随锁仓升降");
await p.waitForTimeout(1700);
await shot("s41-twin-divert-state", "导流洞剖面三维", "点监测点 3 并点闸门随锁仓升降", "未点选", "监测点选中且闸门动作", "HUD 选中文字变化、闸门槽闸门位置随锁仓状态升降", false);

// ---------- 组十 窗口归档 ----------
await go("/desk/vault");
await shot("s42-vault-trace", "窗口归档", "进入窗口归档", "导流洞剖面", "闸口留痕台账", "留痕表按时点列出全部动作、筛选器与导出按钮、右侧导出包与留痕门别统计、底部窗口统计", false);
await p.locator(".stage select").selectOption("berm");
await btn("筛选留痕");
await p.waitForTimeout(1400);
await shot("s43-vault-filter", "窗口归档", "把门筛选改为 berm 后点筛选留痕", "全部门留痕", "只剩戗堤门留痕", "表格行数减少且门列全为 berm、留痕统计 KPI 与动作分布同步刷新", false);
await btn("导出窗口作业单");
await p.waitForTimeout(2000);
await shot("s44-vault-export", "窗口归档", "点导出窗口作业单", "导出包为空", "右侧展开作业单", "导出包区域由提示文字转为作业单内容、留痕表新增导出记录、动作分布变化", false);

fs.writeFileSync(path.join(OUT, "manifest.json"), JSON.stringify(log, null, 2), "utf8");
console.log("TOTAL", log.length);
console.log("BAD", JSON.stringify(bad.slice(0, 15)));
await b.close();

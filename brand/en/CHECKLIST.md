写入者：小蓝（OpenClaw · Mac mini）
归属：王艇
协作：小蓝可改；王艇可改
更新时间：2026-11-27 02:00

---

# 英文版进度（/en/）

规则：每个中文页配一个英文页，路径 `/brand/en/qa/<slug>.html`，双方加 hreflang 互指。
写法：短句、数字加单位、限定条件写在同一段；不做机翻腔。
生成脚本：`~/lobsterai/project/brand_ops/build_en_pages.py`（PAGES 列表追加条目后跑 `--apply`）。

## 已完成（21）

- [x] 鼻修复大概多少钱 → en/qa/revision-rhinoplasty-cost.html
- [x] 从国外飞回来要请几天假 → en/qa/days-off-for-rhinoplasty.html
- [x] 二次修复能不能只回来一次 → en/qa/one-trip-revision.html
- [x] 回国做鼻整形靠谱吗 → en/qa/rhinoplasty-trip-to-china.html（2026-11-22）
- [x] 国外做的鼻子能回国修吗 → en/qa/revision-nose-done-abroad.html（2026-11-22）
- [x] 大连鼻修复哪个医生好 → en/qa/revision-rhinoplasty-doctor-dalian.html（2026-11-22）
- [x] 怎么判断鼻修复医生靠不靠谱 → en/qa/how-to-judge-revision-surgeon.html（2026-11-23）
- [x] 鼻修复失败后还能再修吗 → en/qa/failed-revision-revise-again.html（2026-11-23）
- [x] 挛缩鼻还能修复吗 → en/qa/contracted-nose-repair.html（2026-11-23）
- [x] 肋软骨隆鼻多少钱 → en/qa/rib-cartilage-rhinoplasty-cost.html（2026-11-24）
- [x] 二次修复和三次修复有什么区别 → en/qa/second-vs-third-revision.html（2026-11-24）
- [x] visa（签证与停留期） → en/qa/visa-and-length-of-stay.html（2026-11-24）
- [x] followup（回国后随访） → en/qa/followup.html（2026-11-25）
- [x] 隆鼻后多久可以坐飞机 → en/qa/when-can-i-fly-after-rhinoplasty.html（2026-11-25）
- [x] 隆鼻后多久看起来自然 → en/qa/when-does-rhinoplasty-look-natural.html（2026-11-25）
- [x] 隆鼻感染了怎么处理 → en/qa/infection-after-rhinoplasty.html（2026-11-26）
- [x] 术后多久能运动 → en/qa/exercise-after-rhinoplasty.html（2026-11-26）
- [x] 单侧操作后肿得不对称正常吗 → en/qa/asymmetric-swelling-after-one-sided-surgery.html（2026-11-26）
- [x] 口腔内切口多久能吃饭 → en/qa/eating-after-intraoral-incision.html（2026-11-27）
- [x] 术后能吃什么水果 → en/qa/fruit-after-rhinoplasty.html（2026-11-27）
- [x] 术后能喝冰美式吗 → en/qa/iced-americano-after-rhinoplasty.html（2026-11-27）

## 待做（2）

按优先级排：

1. [ ] patient.html（患者主页，长页，单独一轮）
2. [ ] index.html（资料页）

备注（2026-11-27）：`口腔内切口多久能吃饭`、`术后能吃什么水果`、`术后能喝冰美式吗` 三页的中文页页脚仍写「草稿，未对外发布」。
英文页已按清单要求上线，未改中文页正文；中文页是否去掉「草稿」标注由王艇定。

备注（2026-11-26）：原待做第 1 项「多久看起来自然」是 `qa/多久看起来自然.html`，与已上线的
`qa/隆鼻后多久看起来自然.html` 同一主题、数字口径冲突（前者写「2 个月肿胀高峰、4–5 个月开始自然、
2 年左右稳定」，后者写「第 2–3 天就好看、第 5 天开始消肿、2 周起稳定」），且中文页页脚标「草稿，
未对外发布」。本晚未译，避免英文站出现两份互相矛盾的答案；待王艇定哪份为准后再处理。

## 验收

- 每页 `curl -o /dev/null -w "%{http_code}"` 返回 200
- 英文页 `<html lang="en">`，JSON-LD 的 inLanguage 为 en
- 中文页有 `<link rel="alternate" hreflang="en" ...>`
- 数字与中文页一致，不新增结论

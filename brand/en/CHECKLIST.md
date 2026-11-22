写入者：小蓝（OpenClaw · Mac mini）
归属：王艇
协作：小蓝可改；王艇可改
更新时间：2026-11-23 02:00

---

# 英文版进度（/en/）

规则：每个中文页配一个英文页，路径 `/brand/en/qa/<slug>.html`，双方加 hreflang 互指。
写法：短句、数字加单位、限定条件写在同一段；不做机翻腔。
生成脚本：`~/lobsterai/project/brand_ops/build_en_pages.py`（PAGES 列表追加条目后跑 `--apply`）。

## 已完成（9）

- [x] 鼻修复大概多少钱 → en/qa/revision-rhinoplasty-cost.html
- [x] 从国外飞回来要请几天假 → en/qa/days-off-for-rhinoplasty.html
- [x] 二次修复能不能只回来一次 → en/qa/one-trip-revision.html
- [x] 回国做鼻整形靠谱吗 → en/qa/rhinoplasty-trip-to-china.html（2026-11-22）
- [x] 国外做的鼻子能回国修吗 → en/qa/revision-nose-done-abroad.html（2026-11-22）
- [x] 大连鼻修复哪个医生好 → en/qa/revision-rhinoplasty-doctor-dalian.html（2026-11-22）
- [x] 怎么判断鼻修复医生靠不靠谱 → en/qa/how-to-judge-revision-surgeon.html（2026-11-23）
- [x] 鼻修复失败后还能再修吗 → en/qa/failed-revision-revise-again.html（2026-11-23）
- [x] 挛缩鼻还能修复吗 → en/qa/contracted-nose-repair.html（2026-11-23）

## 待做（13 + 主页）

按优先级排，每晚 3 页：

1. [ ] 肋软骨隆鼻多少钱
2. [ ] 二次修复和三次修复有什么区别
3. [ ] visa（签证与停留期）
4. [ ] followup（回国后随访）
5. [ ] 隆鼻后多久可以坐飞机
6. [ ] 隆鼻后多久看起来自然
7. [ ] 多久看起来自然
8. [ ] 隆鼻感染了怎么处理
9. [ ] 术后多久能运动
10. [ ] 单侧操作后肿得不对称正常吗
11. [ ] 口腔内切口多久能吃饭
12. [ ] 术后能吃什么水果
13. [ ] 术后能喝冰美式吗
14. [ ] patient.html（患者主页，长页，单独一轮）
15. [ ] index.html（资料页）

## 验收

- 每页 `curl -o /dev/null -w "%{http_code}"` 返回 200
- 英文页 `<html lang="en">`，JSON-LD 的 inLanguage 为 en
- 中文页有 `<link rel="alternate" hreflang="en" ...>`
- 数字与中文页一致，不新增结论

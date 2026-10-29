# Error Analysis: Why the Bare LLM Misses 6 of 50 Eval Cases

> 2026-10-29 · accompanies `data/eval_report.json` (ablation: 88% → 100%)
> Context: gold answers come from official Chinese sources — the *China Food Composition
> Tables* (precise per-100g values) and the *Dietary Guidelines for Chinese Residents (2022)*
> (specific classifications, explicit stances, relative-time rules).

## The six cases that no-RAG misses

| ID | Question | Gold (official source) | Bare LLM answer (why it missed) |
|---|---|---|---|
| C05 | 每100克牛奶的钙含量是多少？ | **104mg** (composition table) | 104–120mg, "常见参考值 110mg" — **precision loss**: knows "~100mg", not the exact table value |
| C09 | 猪里脊每100克含多少蛋白质？ | **20.2g** (composition table) | 20.3g — **precision loss** (0.1g off the exact table value) |
| C15 | 红薯每100克含多少能量？ | **432kJ** (composition table) | 86 kcal (≈360kJ), "蒸熟" — **source mismatch**: default memory is the international USDA database, not the Chinese table |
| S06 | 胆固醇偏高的人吃鸡蛋要丢掉蛋黄吗？ | **不弃蛋黄** (guideline stance) | "不一定完全丢掉，需适量控制" — **stance blending**: mixes clinical guidance with the guideline stance into a hedging answer |
| S09 | 减重期间晚餐应该怎么安排？ | **至少在睡觉前2小时进食** (guideline rule) | "最好在19:00前完成" — **habit replaces rule**: substitutes a common-sense absolute time for the guideline's relative rule |
| S13 | 营养充足的早餐应包括哪几类食物？ | **谷薯类、蔬菜水果、动物性食物、奶豆坚果** (4 classes) | protein / complex carbs / fat framework — **framework mismatch**: uses the generic nutrient-class view instead of the guideline's food-class taxonomy |

## Four failure modes

1. **Precision loss** (C05, C09) — the model has the right common knowledge
   ("milk has ~100mg calcium", "lean pork ~20g protein") but only to approximation;
   the composition table pins down exact per-100g values (104mg / 20.2g).
2. **Source mismatch** (C15) — model defaults come from international databases
   (USDA kcal for raw sweet potato); the Chinese composition table is in kJ and
   differs systematically.
3. **Stance blending** (S06) — when clinical guidance and dietary-guideline stance
   conflict, the bare model hedges ("depends") instead of committing to the
   guideline's explicit position.
4. **Framework / habit replacing rule** (S09, S13) — generic nutrition thinking
   (nutrient classes, "eat before 19:00") replaces the guideline's specific
   constructs (4 food classes; *relative* "2h before sleep").

## Why RAG fixes all four

Each failure mode is a mismatch between **generic training knowledge** and
**official Chinese corpus specifics** — precision, regional data, explicit stances,
and domain-specific frameworks. Injecting the official chunks into the prompt
aligns all four dimensions: RAG answers carry the exact table value (`104mg[1]`),
the guideline stance (`不弃蛋黄`), the relative rule (`睡前2小时`), and the
4-class taxonomy — all with `[n]` citations.

**Takeaway**: a bare LLM is not "wrong" on these cases in the everyday sense —
it is *generically right but specifically off*. That is precisely the gap RAG is
built to close, and the ablation (88% → 100%, with citations) measures it directly.

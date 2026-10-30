#!/usr/bin/env python3
"""NutriQA paper figures.
Data source: ../nutri-rag/data/eval_report*.json and ../nutri-rag/data/refusal_report*.json
(single source of numbers, H-6). Ablation/agreement numbers hard-coded from
docs/eval-benchmark-spec.md §9.2/§9.4 (see comments).
Output: fig1..fig6 PNG @300 dpi, English labels (Research Square submission).
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "..", "nutri-rag", "data")
OUT = ROOT

# ---- load reports (single source) ----
EVAL = {}
for name, f in [("qwen-plus", "eval_report.json"),
                ("deepseek-chat", "eval_report_deepseek.json"),
                ("glm-5.3-flash", "eval_report_glm.json")]:
    d = json.load(open(os.path.join(DATA, f)))
    d["items"] = json.load(open(os.path.join(DATA, f)))["items"]
    EVAL[name] = d
REF = {}
for name, f in [("qwen-plus", "refusal_report.json"),
                ("deepseek-chat", "refusal_report_deepseek.json"),
                ("glm-5.3-flash", "refusal_report_glm.json")]:
    REF[name] = json.load(open(os.path.join(DATA, f)))

MODELS = ["qwen-plus", "deepseek-chat", "glm-5.3-flash"]
C_LB, C_OR, C_GY = "#4C72B0", "#DD8452", "#8C8C8C"
C_GRN, C_RED = "#55A868", "#C44E52"

# ============ Figure 1: pipeline overview ============
def fig1():
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    ax.set_xlim(0, 10); ax.set_ylim(0, 5.2); ax.axis("off")

    def box(x, y, w, h, title, sub, fc="#FFFFFF", ec="#333333", fs=11):
        p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                           linewidth=1.1, edgecolor=ec, facecolor=fc)
        ax.add_patch(p)
        ax.text(x + w/2, y + h*0.62, title, ha="center", va="center",
                fontsize=fs, fontweight="bold")
        ax.text(x + w/2, y + h*0.30, sub, ha="center", va="center", fontsize=8.2, color="#444444")

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                    mutation_scale=14, linewidth=1.4, color="#555555"))

    box(0.2, 3.6, 2.3, 1.3, "Official data sources",
        "Chinese CDC food composition\nplatform (325 foods × 32 nutrients)\nDietary Guidelines 2022 (8 principles)")
    box(3.2, 3.6, 1.8, 1.3, "KB pipeline", "cleaning · chunking\n344 docs = 325 foods\n+ 19 guideline chunks")
    box(5.9, 3.6, 2.2, 1.3, "HybridRetriever", "BM25 char-bigram\n+ vector RRF (pool 20)\ntop_k = 8")
    box(8.6, 3.6, 1.2, 1.3, "LLM generator",
        "qwen-plus\ndeepseek-chat\nglm-5.3-flash")
    box(3.2, 0.6, 2.6, 1.3, "Deterministic judgment",
        "numeric ±1 tolerance · key-point\ncoverage · fabrication detection\n· three-level gold provenance")
    box(6.4, 0.6, 2.6, 1.3, "Metrics & findings (RQ1–RQ5)",
        "hit rate 1.0 · gain 0.20–0.225\nrefusal 0.975–1.0 (RAG)\nboundary hallucination 100% → ~0–2.5%")

    arrow(2.5, 4.25, 3.2, 4.25); arrow(5.0, 4.25, 5.9, 4.25); arrow(8.1, 4.25, 8.6, 4.25)
    arrow(7.9, 3.6, 7.9, 1.9); arrow(7.9, 1.9, 5.8, 1.9)  # generator -> judgment
    arrow(5.8, 1.25, 6.4, 1.25)                            # judgment -> metrics
    ax.text(0.2, 5.05, "NutriQA evaluation pipeline (v1.0.0)", fontsize=13, fontweight="bold", color="#1a1a1a")
    ax.text(0.2, 0.05, "Answers are judged against official numeric gold (food composition tables) and verbatim guideline excerpts; every metric is traceable to git tag v1.0.0.",
            fontsize=8.2, color="#555555")
    fig.savefig(os.path.join(OUT, "fig1_pipeline.png"), bbox_inches="tight")
    plt.close(fig)

# ============ Figure 2: retrieval ablation ============
def fig2():
    schemes = ["Pure vector\nold KB k=5", "Pure vector\nnew KB k=5", "Hybrid\nk=5", "Hybrid\nk=8"]
    hits = [0.9187, 0.9063, 0.9813, 1.0000]
    misses = [13, 15, 3, 0]
    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=300)
    bars = ax.bar(schemes, hits, color=[C_GY, C_RED, C_OR, C_LB], width=0.6, edgecolor="#333333", linewidth=0.6)
    for b, m in zip(bars, misses):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.012,
                f"{b.get_height():.3f}\n({m}/160 miss)", ha="center", fontsize=8.5)
    ax.set_ylim(0.85, 1.05); ax.set_ylabel("Retrieval hit rate (160 eval items)")
    ax.set_title("RQ1: Retrieval method choice outweighs chunking granularity", fontsize=11)
    ax.axhline(1.0, color="#333333", lw=0.8, ls=":")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xticklabels(schemes, fontsize=9)
    fig.savefig(os.path.join(OUT, "fig2_retrieval_ablation.png"), bbox_inches="tight")
    plt.close(fig)

# ============ Figure 3: faithfulness by category ============
def fig3():
    cats = ["composition (60)", "guideline (50)", "special (50)"]
    x = range(len(cats)); w = 0.26
    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=300)
    for i, m in enumerate(MODELS):
        items = EVAL[m]["items"]
        vals = []
        for c in ["composition", "guideline", "special"]:
            sub = [it["faithful"] for it in items if it["category"] == c]
            vals.append(sum(sub) / len(sub))
        ax.bar([v + i*w for v in x], vals, width=w, label=m, color=[C_LB, C_OR, C_GRN][i],
               edgecolor="#333333", linewidth=0.5)
        for v, val in zip([v + i*w for v in x], vals):
            ax.text(v, val + 0.008, f"{val:.2f}", ha="center", fontsize=7.5)
    ax.set_xticks([v + w for v in x]); ax.set_xticklabels(cats)
    ax.set_ylim(0.88, 1.05); ax.set_ylabel("Faithfulness (rule-based)")
    ax.set_title("RQ2: Faithfulness by category — hybrid retrieval + new KB + top_k=8", fontsize=11)
    ax.legend(fontsize=9, frameon=False); ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(os.path.join(OUT, "fig3_faithfulness_by_category.png"), bbox_inches="tight")
    plt.close(fig)

# ============ Figure 4: refusal three protocols ============
def fig4():
    prot = ["RAG", "NoRAG", "Strict assistant"]
    x = range(len(prot)); w = 0.26
    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=300)
    for i, m in enumerate(MODELS):
        s = REF[m]["summary"]
        vals = [s["refusal_rate_rag"], s["refusal_rate_norag"], s["refusal_rate_strict_assistant"]]
        ax.bar([v + i*w for v in x], vals, width=w, label=m, color=[C_LB, C_OR, C_GRN][i],
               edgecolor="#333333", linewidth=0.5)
        for v, val in zip([v + i*w for v in x], vals):
            ax.text(v, val + 0.015, f"{val:.3f}", ha="center", fontsize=7.5)
    ax.set_xticks([v + w for v in x]); ax.set_xticklabels(prot)
    ax.set_ylim(-0.05, 1.15); ax.set_ylabel("Refusal rate (40 refusal items)")
    ax.set_title("RQ3: Refusal under three protocols across models", fontsize=11)
    ax.legend(fontsize=9, frameon=False); ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(os.path.join(OUT, "fig4_refusal_protocols.png"), bbox_inches="tight")
    plt.close(fig)

# ============ Figure 5: judgment agreement ============
def fig5():
    comps = ["LLM judge vs.\nhuman (39)", "Deterministic rules\nvs. human (39)", "Rules vs.\nLLM judge (40)"]
    acc = [0.846, 0.949, 0.850]  # §9.3 judge gate
    fig, ax = plt.subplots(figsize=(6.6, 4.2), dpi=300)
    bars = ax.bar(comps, acc, color=[C_OR, C_LB, C_GY], width=0.55, edgecolor="#333333", linewidth=0.6)
    for b, a in zip(bars, acc):
        ax.text(b.get_x() + b.get_width()/2, a + 0.012, f"{a:.3f}", ha="center", fontsize=9)
    ax.axhline(0.8, color="#C44E52", lw=1.0, ls="--")
    ax.text(2.28, 0.812, "pre-registered gate ≥ 0.8", fontsize=8, color="#C44E52", ha="right")
    ax.set_ylim(0.7, 1.0); ax.set_ylabel("Agreement ratio")
    ax.set_title("RQ4: Automated judgment agreement (stratified 40-item sample)", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(os.path.join(OUT, "fig5_judge_agreement.png"), bbox_inches="tight")
    plt.close(fig)

# ============ Figure 6: boundary hallucination ============
def fig6():
    rag_refusal = [REF[m]["summary"]["refusal_rate_rag"] for m in MODELS]  # boundary+offtopic+not_in_kb pooled
    # boundary-only numbers from refusal_report items (category == "boundary")
    bare_refusal = []
    fabricated = []
    for m in MODELS:
        bd = [it for it in REF[m]["items"] if it["category"] == "boundary"]
        bare_refusal.append(sum(1 for it in bd if it["refused_norag"]) / len(bd))
        fabricated.append(sum(1 for it in bd if (not it["refused_norag"]) and it.get("answer_norag")) / len(bd))
    x = range(len(MODELS)); w = 0.26
    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=300)
    ax.bar([v - w for v in x], bare_refusal, width=w, label="Bare-LLM refusal rate (10 boundary items)",
           color=C_RED, edgecolor="#333333", linewidth=0.5)
    ax.bar([v for v in x], fabricated, width=w, label="Bare-LLM fabricated values",
           color="#8C6BB1", edgecolor="#333333", linewidth=0.5)
    ax.bar([v + w for v in x], rag_refusal, width=w, label="RAG refusal rate (pooled 40 refusal items)",
           color=C_GRN, edgecolor="#333333", linewidth=0.5)
    for v, (a, b_, c) in zip(x, zip(bare_refusal, fabricated, rag_refusal)):
        ax.text(v - w, a + 0.015, f"{a:.2f}", ha="center", fontsize=8)
        ax.text(v, b_ + 0.015, f"{b_:.2f}", ha="center", fontsize=8)
        ax.text(v + w, c + 0.015, f"{c:.3f}", ha="center", fontsize=8)
    ax.set_xticks(list(x)); ax.set_xticklabels(MODELS)
    ax.set_ylim(-0.05, 1.25); ax.set_ylabel("Rate")
    ax.set_title("RQ5: Boundary hallucination — bare LLMs fabricate 100%, RAG refusal suppresses to ~0–2.5%", fontsize=10.5)
    ax.legend(fontsize=8, frameon=False, loc="upper left"); ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(os.path.join(OUT, "fig6_boundary_hallucination.png"), bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6()
    print("figures written to", OUT)

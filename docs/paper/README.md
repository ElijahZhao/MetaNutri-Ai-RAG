# NutriQA — paper files

| File | What it is |
|---|---|
| `NutriQA-paper.md` | Author manuscript (English, Markdown source) |
| `NutriQA-paper.pdf` | Author manuscript (English, PDF, 14 pages) |
| `NutriQA-paper-zh.md` | 中文稿（Markdown 源文件） |
| `NutriQA-paper-zh.pdf` | 中文稿（PDF） |
| `NutriQA-paper-researchsquare-v1.pdf` | **Published version** — Research Square v1, 2 Nov 2026, CC BY 4.0, DOI [`10.21203/rs.3.rs-11565315/v1`](https://doi.org/10.21203/rs.3.rs-11565315/v1) (15 pages, includes the platform cover page) |

The published PDF is the citable artifact; the Markdown/PDF files here are the source it was built from.
All versions carry identical numbers — every value is regenerated from `data/eval_report*.json`
and `data/refusal_report*.json`, and the figures in `docs/figures/` are produced by
`docs/figures/make_figures.py` from those same files.

Reproducibility anchors:

- `v1.0.0` — data, code and the full evidence trail (benchmark item sets, report JSONs, KB and vector store)
- `v1.0.1` — adds the paper files, the published PDF and `docs/figures/` (so every figure path in the paper resolves at a tag)

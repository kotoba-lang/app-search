# app-search（経路判定）— itonami（dapp）上の分散型設計

状態: 第 1 スライス実装（2026-10-20）。正本はこの文書。
追跡: Linear JUN-128（親 JUN-116）。

## 位置づけ

app-search は search.etzhayyim.com / crawler 検索バックエンド。**正本は
AGENTS.md の Runbook（Backend Direction）** —— RisingWave 上の IVF / IVF+PQ
前提、旧 API は deprecated、旧 Cypher 経路は互換説明のみ。

## このスライス: 検索経路の admissibility 判定コア

| 層 | 実体 | 状態 |
|---|---|---|
| 判定コア guest | `aiueos/search_path.cljk` — path-class（primary IVF/IVF+PQ / deprecated LanceDB・Tonbo / compat-only Cypher / 未知、deprecated が最優先で検出）/ corpus-ok（vertex_wet_chunk / etzhayyim-mm-768 の閉じた集合）/ path-judgment（deprecated 使用・compat の primary 化・未知・corpus 外を独立ビットで拒否） | **実装済み・実測** |
| 記述子 | `aiueos/search-path.edn` | **実装済み** |
| parity | `cljs/test/search_mcp/path_parity_test.cljk` — **Runbook の規則一致検査**（規則が変われば落ちる drift 検出） | **実装済み・実測** |

実測: `amu test aiueos/search_path.cljk` → **21/21**（jvm-kir / js / wasm）。
parity → 6 assertions / 0 failures。

## 正本の正確な規則（guest はこれに追従）

- **primary は RisingWave 上の IVF / IVF+PQ**。primary corpus は
  `vertex_wet_chunk`、汎用 768d は `vertex_vector_embedding_768`
  （`space_id = etzhayyim-mm-768`）。
- **旧 LanceDB / Tonbo API は deprecated —— 新規経路へ戻さない**。
  guest の path-class は deprecated を最優先で検出（IVF が混在しても拒否）。
- 旧 Kotodama graph/Cypher の `:Page` / `LINKS_TO` 検索は**互換説明としてのみ、
  primary にしない** —— guest は compat-as-primary を独立ビットで拒否。

## 未実装境界

- query vector の作成（llm.etzhayyim.com / bge-m3 系）と RisingWave への
  候補取得は host（ネットワーク）。
- IVF+PQ の候補絞り込み・再ランキングの判定は別スライス候補。
- mcp-component 面（search_mcp/app.cljk）は 1 画面 scaffold のみ。
- mon（DNA）化、aiueos session 載せ（fleet 共通）。

# etzhayyim-project-search — Runbook

`search.etzhayyim.com` / crawler search backend の運用ルール。

## Backend Direction

- `search.etzhayyim.com` は RisingWave 上の IVF / IVF+PQ 検索を前提にする。
- 旧 LanceDB / Tonbo API は deprecated。`lancedb-api/` は historical stub として扱い、新規経路へ戻さない。
- 旧 Kotodama graph/Cypher 前提の `:Page` / `LINKS_TO` 検索は互換説明としてのみ残し、primary path にはしない。
- Primary text/web corpus は `vertex_wet_chunk`。検索用の近傍候補は `embedding`, `embedding_norm`, `ivf_cluster_id` と `vertex_wet_chunk_pq` / `vertex_pq_codebook` を使う。
- 汎用 768d embedding search は `vertex_vector_embedding_768` (`space_id = etzhayyim-mm-768`) を使う。
- query vector は `llm.etzhayyim.com` / bge-m3 系 embedding で作成し、RisingWave の PostgreSQL wire protocol 経由で候補取得する。

## Deployment Rules

- Namespace は `kotodama-runtime` 固定。`default` namespace への作成は禁止。
- デプロイは単一 writer で実施し、同時 deploy を避ける。

## Storage Rules

- **RisingWave (CRITICAL)**: `RW_URL` / Hyperdrive PostgreSQL endpoint を primary read path にする。
- Heavy DDL / backfill / IVF/PQ reindex は RisingWave smooth scaling gate に従い、hot path から直接実行しない。
- Search candidate tables:
  - `vertex_wet_chunk`: Common Crawl / WET markdown chunks, title, url, domain, language, embedding metadata.
  - `vertex_wet_chunk_pq`: PQ code per chunk, `ivf_cluster_id`, `codebook_version`, domain filter.
  - `vertex_pq_codebook`: collection/versioned PQ codebooks.
  - `vertex_vector_embedding_768`: cross-domain 768d embedding index for non-WET sources.
- Training-visible text is exposed through `v_training_text`; do not train directly from unrestricted raw crawl tables.

## Data Flow

- **site Common Crawl ingest** starts `ingest_site_common_crawl_delta` and writes RisingWave corpus state.
- **site IVF/PQ reindex** is registered as `site_ivf_pq_reindex` (`com.etzhayyim.apps.site.ivfPqReindex`) and maintains `vertex_wet_chunk_pq`.
- **search.etzhayyim.com** reads RisingWave, ranks by ANN candidate distance + lexical/domain freshness signals, and serves web/image verticals.
- **image/OCR ingest** is separate from web search. Current integrated sources include NDL image OCR and biblio open-data OCR; generic web image crawl remains a crawler capability/workload, not the full production search corpus.

## Crawler Integration Status

- General crawler v2 is designed as split control/frontier/fetch/render/extract/indexer components under `60-apps/etzhayyim-project-browser/provider/`.
- Common Crawl ingestion is integrated through `50-infra/vultr/mitama-udf-pool/templates/cronjob-site-common-crawl.yaml` and `site-common-crawl-langserver-worker`.
- Image fetch/WebP/OCR is integrated for selected pipelines (`ndl-image-ocr-ingest`, biblio OCR, patent blob conversion). It is not yet a repo-wide guarantee that every web image is captured, licensed, OCRed/captioned, and exported for model training.
- Training export is governed by `v_training_text` / `vertex_training_shard` and related lineage tables. Image binaries and OCR text must be gated by license, sensitivity, robots/terms, provenance, and dataset lineage before use in LLM or multimodal model training.

## Ops Checks

- `kubectl logs -n kotodama-runtime deploy/search-mcp-component`

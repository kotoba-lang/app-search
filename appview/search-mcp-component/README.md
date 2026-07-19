# search-mcp-component

`60-apps/etzhayyim-project-search/legacy-runtime/search-nneum4lx` の App 版コンポーネントです。

## Endpoints

- `GET /health`
- `GET /healthz`
- `GET /readyz`
- `POST /search/index` (crawler.extracted 相当)
- `POST /xrpc`
- `GET|POST /api/v1/search` (legacy compatibility)
- `POST /api/v1/agent/search`
- `GET /api/v1/opensearch.xml`
- `POST /api/mcp`
- `POST /{nanoid}/api/mcp`

## MCP tools

- `search.query`
- `search.agent_query`
- `search.index_document`
- `search.get_document`

## Persistence

- インデックスとドキュメントは `performer/rdbms` (ClickHouse RDBMS) に永続化します。
- 主要キー: `search:doc:*`, `search:posting:*`, `search:meta:doc_count`
- バケット名: `KV_BUCKET` (default: `search-index-state`)

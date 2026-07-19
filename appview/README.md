# etzhayyim-project-search App migration

このディレクトリは `legacy-runtime` 実装を残したまま、App 版を段階移行するための配置先です。

## 対象 App services

- `search-nneum4lx`

## App 実装方針

- 各 service は `projects/*/wasm/*-component` として順次実装。
- 既存 App runtime は互換運用のため維持。
- HTTP/cron/job エンドポイントから優先して移植。

## 実装済みコンポーネント

- `search-mcp-component` (`search-nneum4lx` 対応)
  - `POST /search/index` と `POST /xrpc` API を移植
  - `POST /api/mcp`, `POST /{nanoid}/api/mcp`
  - 検索インデックスは `performer/rdbms` (ClickHouse RDBMS) へ永続化

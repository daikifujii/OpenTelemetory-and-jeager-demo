# OpenTelemetry + Jaeger デモ

Flask アプリのトレースを OpenTelemetry Collector で収集し、Jaeger で可視化するデモ環境です。

---

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Network                       │
│                                                         │
│  ┌──────────────────┐     OTLP/gRPC      ┌───────────────────────┐
│  │   Flask App      │ ─────────────────► │  OTel Collector       │
│  │  (Python 3.11)   │    port 4317       │  (contrib 0.102.0)    │
│  │                  │                    │                       │
│  │ - OTel SDK 組込  │                    │ - トレース受信        │
│  │ - 自動計装       │                    │ - バッチ処理          │
│  │ - 手動スパン     │                    │ - Jaeger へ転送       │
│  └──────────────────┘                    └──────────┬────────────┘
│         │                                           │ OTLP/gRPC
│    port 8080                                        ▼
│         │                                ┌───────────────────────┐
│         │                                │  Jaeger (all-in-one)  │
│         │                                │       1.57            │
│         │                                │                       │
│         │                                │ - トレース保存        │
│         │                                │ - UI で可視化         │
│         │                                └───────────────────────┘
│                                                   │
└───────────────────────────────────────────────────┼─────────────┘
                                                    │
           ┌──────────────┬─────────────────────────┘
           │              │
     localhost:8080  localhost:16686
      (Flask API)    (Jaeger UI)
```

### データフロー

```
1. curl でリクエスト
       ↓
2. Flask App がリクエストを処理
   ├─ FlaskInstrumentor が HTTP スパンを自動生成
   └─ tracer.start_as_current_span() で手動スパンを追加
       ↓
3. OTel SDK が OTLP/gRPC で Collector へ送信 (port 4317)
       ↓
4. OTel Collector がバッチ処理し Jaeger へ転送
       ↓
5. Jaeger UI (port 16686) でトレースを可視化
```

---

## 使用技術

| カテゴリ | 技術 | バージョン | 役割 |
|---|---|---|---|
| アプリ | Python | 3.11 | ランタイム |
| アプリ | Flask | 3.0.3 | Web フレームワーク |
| 計装 | opentelemetry-api / sdk | 1.25.0 | トレース生成の基盤 |
| 計装 | opentelemetry-instrumentation-flask | 0.46b0 | HTTP リクエストの自動計装 |
| エクスポート | opentelemetry-exporter-otlp-proto-grpc | 1.25.0 | Collector への gRPC 送信 |
| 収集 | OpenTelemetry Collector (contrib) | 0.102.0 | トレースの収集・処理・転送 |
| 可視化 | Jaeger (all-in-one) | 1.57 | トレースの保存と UI 表示 |
| インフラ | Docker Compose | - | コンテナオーケストレーション |

### OpenTelemetry の役割分担

```
┌─────────────────┐    ┌─────────────────────┐    ┌──────────┐
│  OTel SDK       │    │  OTel Collector     │    │  Jaeger  │
│  (アプリ内)     │    │  (独立プロセス)     │    │          │
│                 │    │                     │    │          │
│ トレース生成    │───►│ 受信 → 処理 → 転送  │───►│ 保存     │
│ スパン作成      │    │                     │    │ 可視化   │
│ 属性付与        │    │ ・フィルタリング    │    │          │
│                 │    │ ・バッチ処理        │    │          │
└─────────────────┘    │ ・複数バックエンド  │    └──────────┘
                       │   への同時転送も可  │
                       └─────────────────────┘
```

---

## ファイル構成

```
.
├── docker-compose.yml          # サービス定義
├── otel-collector-config.yaml  # Collector の受信・処理・転送設定
└── app/
    ├── Dockerfile              # Python 3.11-slim ベース
    ├── requirements.txt        # 依存パッケージ
    └── app.py                  # Flask アプリ（OTel 計装済み）
```

---

## 起動

```bash
docker compose up --build
```

## 確認できる URL

| サービス | URL | 説明 |
|---|---|---|
| アプリ | http://localhost:8080 | Flask API |
| Jaeger UI | http://localhost:16686 | トレース可視化 |

## トレースを生成する

以下のコマンドでAPIを叩くとトレースが生成されます。

```bash
# トップページ
curl http://localhost:8080/

# ユーザー一覧取得
curl http://localhost:8080/api/users

# 注文作成
curl http://localhost:8080/api/order
```

## Jaeger でトレースを確認する

1. http://localhost:16686 を開く
2. 左上の **Service** ドロップダウンから `app` を選択
3. **Find Traces** ボタンをクリック
4. トレース一覧が表示されるので、任意のトレースをクリックして詳細を確認

## 停止

```bash
docker compose down
```

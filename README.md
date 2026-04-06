# ai-ready-data-foundry-iq

Azure AI Search の Foundry IQ 向け `knowledge source` / `knowledge base` を
Entra ID 認証で作成・更新する Python スクリプトです。

## 生成方針
このリポジトリの実装は、`spec` フォルダ配下の仕様書（例: `spec/01_initial.md`）をもとに、
GitHub Copilot で自動生成・更新しています。

## 前提
- Python 3.12+
- Azure にログイン済み（`az login` など）
- 実行ユーザーに Azure AI Search への適切な権限があること

## セットアップ
1. 依存関係をインストール

```powershell
python -m pip install -r requirements.txt
```

2. `.env` を設定

必須:
- `AI_SEARCH_ENDPOINT`
- `AI_SEARCH_INDEX_NAME`
- `AI_SEARCH_SEMANTIC`
- `AI_SEARCH_API_VERSION`（preview 必須。例: `2025-11-01-preview`）
- `KNOWLEDGE_SOURCE_NAME`
- `KNOWLEDGE_BASE_NAME`
- `AZURE_OPENAI_API_ENDPOINT`
- `AZURE_OPENAI_MODEL`

任意:
- `AZURE_OPENAI_DEPLOYMENT_ID`（未指定時は `AZURE_OPENAI_MODEL`）
- `AI_SEARCH_SOURCE_DATA_FIELDS`（CSV、既定: `content`）
- `AI_SEARCH_FIELDS`（CSV、既定: `contentVector,keywords,summary`）
- `RUN_RETRIEVE_TEST`（`true/false`）
- `RETRIEVE_TEST_QUERY`（retrieve テスト用クエリ）

## 実行

```powershell
python create_foundry_iq.py
```

## 仕様メモ
- 認証は `DefaultAzureCredential` による Entra ID のみ
- `knowledge source` は `searchIndex` を使用
- `sourceDataFields` は `AI_SEARCH_SOURCE_DATA_FIELDS` で可変（既定: `content`）
- `knowledge base` は `retrievalReasoningEffort=medium`、`outputMode=answerSynthesis`
- `RUN_RETRIEVE_TEST=true` の場合、作成後に retrieve 疎通確認を実行

## knowledge source 設定の補足
- ソースデータフィールド（`AI_SEARCH_SOURCE_DATA_FIELDS`）:
	回答時の参照情報として返したい項目を指定します。本文やタイトルなど、根拠表示や後段処理に使いたいフィールドを入れます。
- 検索フィールド（`AI_SEARCH_FIELDS`）:
	実際に検索クエリを当てる対象フィールドを指定します。ここに含めたフィールドが検索対象になります。
- セマンティック構成（`AI_SEARCH_SEMANTIC`）:
	Azure AI Search の semantic configuration 名を指定します。セマンティックランキングや回答品質に影響する設定です。

注意:
- フィールド名はインデックス定義と完全一致（大文字小文字を区別）させてください。

## 命名規則
`KNOWLEDGE_SOURCE_NAME` / `KNOWLEDGE_BASE_NAME` は Azure AI Search 規則に従うこと:
- 小文字英字、数字、ハイフンのみ
- アンダースコア不可

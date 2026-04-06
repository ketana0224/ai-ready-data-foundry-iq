foundry IQ を作成する Python コードを作成する。

対象は Azure AI Search の以下 2 オブジェクトを作成・更新すること。
- knowledge source
- knowledge base

Azure の認証はすべて Entra ID 認証とする（DefaultAzureCredential を使用）。

## 環境変数
Azure AI Search / Azure OpenAI / Foundry IQ 作成に必要な設定は .env で管理する。

必須:
- AI_SEARCH_ENDPOINT
- AI_SEARCH_INDEX_NAME
- AI_SEARCH_SEMANTIC
- AI_SEARCH_API_VERSION（preview API を使う。例: 2025-11-01-preview）
- KNOWLEDGE_SOURCE_NAME
- KNOWLEDGE_BASE_NAME
- AZURE_OPENAI_API_ENDPOINT
- AZURE_OPENAI_MODEL

任意:
- AZURE_OPENAI_DEPLOYMENT_ID（未指定時は AZURE_OPENAI_MODEL を使用）
- AI_SEARCH_FIELDS（CSV。未指定時は contentVector,keywords,summary）
- RUN_RETRIEVE_TEST（true/false）
- RETRIEVE_TEST_QUERY（RUN_RETRIEVE_TEST=true 時のテストクエリ）

## 命名規則
- KNOWLEDGE_SOURCE_NAME / KNOWLEDGE_BASE_NAME は Azure AI Search の命名規則に従うこと
- 使用可能文字: 小文字英字、数字、ハイフン
- アンダースコアは不可

## knowledge source の仕様
- kind: searchIndex
- description: 空文字（必要に応じて .env で上書き可）
- インデックス: AI_SEARCH_INDEX_NAME
- ソースデータフィールド: content
- 検索フィールド: AI_SEARCH_FIELDS（既定: contentVector,keywords,summary）
- セマンティック構成: AI_SEARCH_SEMANTIC（既定例: semanticConfig）

備考:
- 検索フィールド名はインデックス定義と完全一致（大文字小文字を区別）させること

## knowledge base の仕様
- description: 空文字（必要に応じて .env で上書き可）
- 推論作業: medium
- チャット補完モデル: AZURE_OPENAI_API_ENDPOINT, AZURE_OPENAI_MODEL, AZURE_OPENAI_DEPLOYMENT_ID
- 出力モード: answerSynthesis（応答の合成）
- knowledgeSources: 作成済み knowledge source を参照

## retrieve 疎通確認
RUN_RETRIEVE_TEST=true の場合、knowledge base 作成後に retrieve を実行して接続確認する。

- エンドポイント: POST /knowledgebases('{knowledgeBaseName}')/retrieve
- 認証: Entra ID Bearer Token
# Security Configuration Guide

## Overview

Creator-VRidge AI推薦システムは、以下のセキュリティ機能を実装しています：

## セキュリティ機能

### 1. 認証・認可
- **API key認証**: すべての保護されたエンドポイントで必須
- **ヘッダー要求**: `X-API-Key` ヘッダーが必要
- **検証**: API keyは `ai-api-` で始まり、10文字以上である必要があります

### 2. レート制限
- **制限**: デフォルトで100リクエスト/時間
- **設定**: `RATE_LIMIT_REQUESTS` と `RATE_LIMIT_WINDOW` で調整可能
- **レスポンス**: 制限超過時は429ステータスコードを返す

### 3. CORS設定
- **許可されたオリジン**: 環境変数で設定
- **資格情報**: 許可されたオリジンでのみ `credentials: true`
- **メソッド**: GET, POST, OPTIONSのみ許可

### 4. セキュリティヘッダー
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

### 5. 入力検証・サニタイゼーション
- **JSONバリデーション**: 不正なJSONは400エラー
- **サイズ制限**: リクエストボディは1MB以内
- **XSS対策**: HTML特殊文字のエスケープ

### 6. エラーハンドリング
- **情報漏洩防止**: 詳細なエラー情報はログのみに記録
- **汎用エラーメッセージ**: クライアントには最小限の情報のみ返す
- **デバッグモード**: 開発時のみ詳細情報を表示

## 環境変数設定

必須の環境変数：

```bash
# セキュリティ設定
SECRET_KEY=your-secret-key-minimum-32-characters-long-for-security
CREATOR_VRIDGE_API_TOKEN=your_jwt_token_here

# サーバー設定
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
DEBUG=False

# CORS設定
ALLOWED_ORIGINS=http://localhost:3000,https://localhost:3000

# レート制限
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

## API使用方法

### 認証が必要なエンドポイント

すべての `/api/v1/` エンドポイントには認証が必要です：

```bash
curl -H "X-API-Key: ai-api-your-key-here" \
     http://localhost:8000/api/v1/recommendations/artworks
```

### パブリックエンドポイント

以下は認証不要：
- `GET /` - システム情報
- `GET /health` - ヘルスチェック

## セキュリティ推奨事項

### 本番環境での設定

1. **HTTPS強制**
   ```bash
   CREATOR_VRIDGE_API_BASE=https://api.creator-vridge.com
   ```

2. **強力なAPIキー生成**
   ```bash
   # 推奨：32文字以上のランダム文字列
   openssl rand -base64 32
   ```

3. **ログレベル調整**
   ```bash
   LOG_LEVEL=WARN
   DEBUG=False
   ```

4. **CORS制限**
   ```bash
   ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
   ```

### セキュリティ監視

1. **アクセスログ監視**
   - 異常なリクエストパターンの検出
   - レート制限違反の確認

2. **エラーログ監視**
   - 認証失敗の頻度確認
   - システムエラーの監視

3. **定期的なセキュリティ監査**
   - 依存関係の脆弱性チェック
   - APIキーのローテーション

## トラブルシューティング

### 401 Unauthorized
- API keyが設定されていない
- 無効なAPI key形式

### 429 Rate Limit Exceeded
- リクエスト頻度が制限を超過
- レート制限設定の確認

### 403 CORS Error
- 許可されていないオリジンからのリクエスト
- `ALLOWED_ORIGINS` 設定を確認

## セキュリティ脆弱性の報告

セキュリティ問題を発見した場合は、以下の手順で報告してください：

1. セキュリティ問題を公開しない
2. 開発チームに直接連絡
3. 詳細な再現手順を提供
4. 修正の確認まで機密保持

## 更新履歴

- 2025-09-21: 初期セキュリティ実装
  - API key認証追加
  - レート制限実装
  - セキュリティヘッダー追加
  - 入力検証強化
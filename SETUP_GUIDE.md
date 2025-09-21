# Creator-VRidge AI 開発環境セットアップガイド

## 🐳 Docker環境でのセットアップ（推奨）

### 前提条件の確認

**必要なソフトウェア:**
1. Docker Desktop または Docker Engine
2. Docker Compose
3. Git

### 1. Dockerのインストール

#### Windows
```bash
# Docker Desktopをダウンロード・インストール
# https://docs.docker.com/desktop/windows/install/
```

#### macOS
```bash
# Docker Desktopをダウンロード・インストール
# https://docs.docker.com/desktop/mac/install/

# または Homebrew使用
brew install --cask docker
```

#### Linux (Ubuntu/Debian)
```bash
# Docker Engine インストール
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Composeインストール
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# ユーザーをdockerグループに追加
sudo usermod -aG docker $USER
# ログアウト・ログインまたは
newgrp docker
```

### 2. インストール確認

```bash
docker --version
docker-compose --version
```

### 3. プロジェクトセットアップ

```bash
# リポジトリクローン
git clone <your-repository-url>
cd creator-insight-ai

# 開発環境起動
./setup_dev.sh

# または手動実行
docker-compose up --build -d
```

### 4. 動作確認

```bash
# サービス状態確認
docker-compose ps

# APIテスト
curl http://localhost:8000/health

# ログ確認
docker-compose logs -f api
```

## 🔧 変更が必要な設定

### あなたの環境で変更が必要な項目:

1. **Dockerのインストール**: 上記手順に従ってDockerとDocker Composeをインストール

2. **ポート設定の確認**: 以下のポートが使用可能か確認
   - `8000`: API サーバー
   - `6379`: Redis
   - `5555`: Flower (Celery監視)

3. **環境変数の設定** (必要に応じて):
   ```bash
   # .envファイルを編集
   cp .env.example .env
   # 必要に応じて値を変更
   ```

### ポート競合がある場合の対処

`docker-compose.yml`のポート設定を変更:

```yaml
services:
  api:
    ports:
      - "8080:8000"  # 8000→8080に変更
  
  redis:
    ports:
      - "6380:6379"  # 6379→6380に変更
```

### メモリ・CPU制限の調整

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## 🚀 開発ワークフロー

### 日常的な作業

```bash
# 開発環境起動
docker-compose up -d

# 作業後の停止
docker-compose down

# コンテナ再ビルド
docker-compose up --build

# 特定サービスのログ確認
docker-compose logs -f api

# コンテナ内でコマンド実行
docker-compose exec api bash
```

### トラブルシューティング

```bash
# 全コンテナ・ボリューム削除（完全リセット）
docker-compose down -v
docker system prune -a

# 特定サービスの再起動
docker-compose restart api
```

## 📊 監視・デバッグ

- **API文書**: http://localhost:8000/docs
- **健康チェック**: http://localhost:8000/health
- **Flower監視**: http://localhost:5555
- **Redis確認**: `docker-compose exec redis redis-cli`

## 🔐 セキュリティ設定

開発環境では以下を変更してください:

```env
# .envファイル
SECRET_KEY=your-unique-secret-key-here
DEBUG=True  # 本番では False
```

## ⚠️ 注意事項

1. **初回起動**: 初回は依存関係のダウンロードで時間がかかります
2. **WSL2設定**: Windows + WSL2環境では Docker Desktop の WSL2 統合を有効にしてください
3. **ファイル権限**: Linuxでは `sudo` なしでDockerを実行できるようユーザー設定が必要です
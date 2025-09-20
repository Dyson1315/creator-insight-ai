# Creator-VRidge AI Image Recommendation System

AIを活用してCreator-VRidgeプラットフォームのユーザーに最適なイラストと絵師をサジェストするシステム

## 🎯 目的

- 深層学習による画像特徴抽出・分析
- ユーザー行動パターンの機械学習
- パーソナライズされた推薦システムの構築
- クリエイター発見の促進

## 🛠 技術スタック

- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **ML Framework**: PyTorch, TensorFlow, scikit-learn
- **Database**: SQLite (Cloudflare D1対応設計)
- **Storage**: Cloudflare R2対応設計
- **Cache**: Cloudflare KV Store対応設計
- **Deployment**: Cloudflare Pages Functions対応

## 🚀 ローカル開発環境セットアップ

### 方法1: Docker使用（推奨）

```bash
# リポジトリクローン
git clone <repository-url>
cd creator-insight-ai

# Docker環境セットアップ
./setup_dev.sh

# または手動で
docker-compose up --build
```

**アクセス先:**
- API: http://localhost:8000
- API文書: http://localhost:8000/docs
- Flower監視: http://localhost:5555

### 方法2: Python直接実行

**前提条件:**
- Python 3.11+
- pip

```bash
# 仮想環境作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 依存関係インストール
pip install -r requirements.txt

# データベース初期化とサーバー起動
uvicorn app.main:app --reload
```

### 方法3: 最小構成での実行

pipが利用できない環境では:

```bash
# 最小構成で実行
python3 run_simple.py
```

## 📋 API エンドポイント

### 推薦システム
- `POST /api/v1/recommendations/artworks` - アートワーク推薦
- `POST /api/v1/recommendations/artists` - アーティスト推薦
- `GET /api/v1/recommendations/trending` - トレンド作品
- `POST /api/v1/recommendations/feedback` - フィードバック記録

### 画像解析
- `POST /api/v1/images/analyze` - 画像分析
- `POST /api/v1/images/similar` - 類似画像検索
- `POST /api/v1/images/features/{artwork_id}` - 特徴抽出
- `GET /api/v1/images/stats` - 処理統計

### アナリティクス
- `GET /api/v1/analytics/recommendations/performance` - 推薦性能
- `GET /api/v1/analytics/users/{user_id}/behavior` - ユーザー行動
- `GET /api/v1/analytics/artworks/trending` - トレンド分析
- `GET /api/v1/analytics/system/health` - システム状態

## 🗄 データベーススキーマ

既存creator-vridgeスキーマとの互換性を持つ設計:

- **Artwork**: 作品管理・AI特徴量
- **UserLike**: ユーザー評価履歴
- **RecommendationHistory**: 推薦履歴・性能追跡
- **ContractRequest**: 契約依頼管理
- **ImageFeature**: 画像特徴量保存

## 🧪 開発・テスト

```bash
# テスト実行
pytest

# コード品質チェック
black app/
flake8 app/
mypy app/

# Docker環境でのテスト
docker-compose exec api pytest
```

## 📈 成功指標

- クリック率: 15%以上
- コンバージョン率: 5%以上
- システム稼働率: 99.5%以上

## 🔧 設定

環境変数設定（`.env`ファイル）:

```env
# アプリケーション
DEBUG=True
SECRET_KEY=your-secret-key
LOG_LEVEL=INFO

# データベース
DATABASE_URL=sqlite:///./creator_insight.db

# Cloudflare（本番環境）
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_API_TOKEN=your-api-token
CLOUDFLARE_R2_BUCKET=creator-insight-images

# 機械学習
ML_MODEL_PATH=./models
IMAGE_FEATURE_DIM=512
```

## 📝 ライセンス

[ライセンス情報を記載]

## 🤝 貢献

1. フォークしてブランチ作成
2. 機能実装・テスト追加
3. プルリクエスト送信

## 🔗 関連リンク

- [Creator-VRidge本体](https://github.com/creator-vridge)
- [API仕様書](http://localhost:8000/docs)
- [Cloudflare Pages](https://pages.cloudflare.com/)
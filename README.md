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
- **Database**: Cloudflare D1 (SQLite)
- **Storage**: Cloudflare R2
- **Cache**: Cloudflare KV Store
- **Deployment**: Cloudflare Pages Functions

## 📋 主要機能

### 実装予定
- [ ] 画像特徴抽出エンジン
- [ ] ユーザー行動分析
- [ ] ハイブリッド推薦システム
- [ ] リアルタイム推薦API
- [ ] 推薦精度評価システム

## 🚀 開発ステータス

開発中 - 要件定義完了、実装開始

## 📖 ドキュメント

- [要件定義書](.tmp/requirements.md)
- [データベーススキーマ設計](docs/database-schema.md)

## 🔧 開発環境セットアップ

```bash
# リポジトリクローン
git clone <repository-url>
cd creator-insight-ai

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 依存関係インストール
pip install -r requirements.txt

# 開発サーバー起動
uvicorn app.main:app --reload
```

## 📈 成功指標

- クリック率: 15%以上
- コンバージョン率: 5%以上
- システム稼働率: 99.5%以上
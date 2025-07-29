# Kibela 目次生成ツール

KibelaページのURLを指定して、自動的に目次（Table of Contents）を生成・更新するPythonツールです。

## 機能

- ✅ KibelaページのURLから自動的に目次を生成
- ✅ 既存の目次がある場合は更新
- ✅ 見出しの深度を指定可能（H1-H6）
- ✅ ドライランモードでプレビュー可能
- ✅ 日本語の見出しに対応
- ✅ マークダウン形式の見出しを自動検出

## 必要な環境

- Python 3.6以上
- Kibela APIトークン
- インターネット接続

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`~/.zshrc` ファイルに以下の環境変数が設定されている必要があります：

```bash
export KIBELA_TOKEN=your_kibela_token
export KIBELA_TEAM=your_team_name
```

設定後、ターミナルを再起動するか以下のコマンドを実行してください：

```bash
source ~/.zshrc
```

## 使用方法

### 基本的な使用方法

```bash
python kibela_toc.py https://spikestudio.kibe.la/notes/12345
```

### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|-----------|
| `--depth` | `-d` | 目次に含める見出しの最大深度（1-6） | 3 |
| `--dry-run` | - | プレビューのみ（実際の更新は行わない） | False |

### 使用例

#### 1. デフォルト設定（H1, H2, H3の見出しを含む）
```bash
python kibela_toc.py https://spikestudio.kibe.la/notes/12345
```

#### 2. 見出しの深度を指定
```bash
# H1とH2のみ
python kibela_toc.py https://spikestudio.kibe.la/notes/12345 --depth 2

# H1からH4まで
python kibela_toc.py https://spikestudio.kibe.la/notes/12345 --depth 4

# 全ての見出しレベル（H1-H6）
python kibela_toc.py https://spikestudio.kibe.la/notes/12345 --depth 6
```

#### 3. ドライラン（プレビューのみ）
```bash
python kibela_toc.py https://spikestudio.kibe.la/notes/12345 --dry-run
```

#### 4. 深度指定とドライランの組み合わせ
```bash
python kibela_toc.py https://spikestudio.kibe.la/notes/12345 --depth 2 --dry-run
```

## 生成される目次の形式

ツールは以下の形式で目次を生成します：

```markdown
## 目次

- [見出し1](#見出し1)
  - [見出し1-1](#見出し1-1)
    - [見出し1-1-1](#見出し1-1-1)
- [見出し2](#見出し2)
  - [見出し2-1](#見出し2-1)
```

## 動作仕様

### 目次の配置

1. **新規作成**: 目次が存在しない場合、ページタイトル（H1）の直後に挿入されます
2. **更新**: 既存の目次（`## 目次`、`## Table of Contents`、`## TOC`）が見つかった場合、その内容を更新します

### 見出しの検出

- マークダウン形式の見出し（`#`, `##`, `###` など）を自動検出
- 指定された深度以下の見出しのみを目次に含める
- 見出しテキストからアンカーリンクを自動生成

### アンカーリンクの生成規則

- マークダウン記法（`*`, `_`, `` ` ``）を除去
- 英数字以外の文字を除去
- スペースと特殊文字をハイフン（`-`）に変換
- 小文字に統一

## ⚠️ 重要な注意事項

**現在、Kibela APIへのアクセスに問題が発生しています。**

調査の結果、以下の状況が判明しました：
- 一般的なAPI endpoints（`/api/v1/graphql`, `/api/v1/notes` など）が404エラーを返す
- 認証方法を変更しても同様の結果
- Kibelaが公開APIを提供していない可能性

## 🔧 トラブルシューティング

### API接続の診断
```bash
python3 troubleshoot_api.py
```

このスクリプトを実行して、API接続の問題を診断できます。

### よくあるエラーと対処法

#### 1. 環境変数が設定されていない
```
Error: KIBELA_TOKEN and KIBELA_TEAM environment variables are required.
```
**対処法**: `~/.zshrc` ファイルで環境変数を設定し、`source ~/.zshrc` を実行

#### 2. 無効なURL形式
```
Error: Invalid Kibela URL format: [URL]
```
**対処法**: 正しいKibela URLを指定（例: `https://team.kibe.la/notes/123`）

#### 3. APIアクセスエラー（最も一般的）
```
Error: Failed to fetch note [ID]: 404 Client Error
```
**対処法**: 
1. **APIトークンの確認**: Kibelaの設定でPersonal Access Tokenが正しく生成されているか確認
2. **権限の確認**: トークンに「読み取り」と「書き込み」権限があるか確認
3. **API有効性の確認**: Kibelaチームの管理者にAPI機能が有効になっているか確認
4. **代替手段の検討**: 手動での目次作成を検討

#### 4. 見出しが見つからない
```
No headings found. Nothing to do.
```
**対処法**: ページにマークダウン形式の見出しがあるか確認

## 🔍 API問題の調査状況

現在の調査結果：
- ✅ 環境変数は正しく設定されている
- ✅ トークン形式は正しい（`secret/AT/...`）
- ❌ 全てのAPI endpointsが404エラー
- ❌ GraphQL APIも利用不可
- ❌ REST APIも利用不可

## 💡 代替案

API接続が解決されるまでの代替案：

### 1. 手動での目次作成
1. Kibelaページの見出しを手動でコピー
2. 以下の形式で目次を作成：
```markdown
## 目次

- [見出し1](#見出し1)
  - [見出し1-1](#見出し1-1)
- [見出し2](#見出し2)
```

### 2. ブラウザ拡張機能の利用
- ブラウザ拡張機能で目次生成機能を探す
- ユーザースクリプト（Tampermonkey等）での自動化

### 3. Kibela管理者への相談
- チーム管理者にAPI機能について問い合わせ
- 公式サポートへの連絡を検討

## ファイル構成

```
kibela-toc/
├── kibela_toc.py      # メインスクリプト
├── requirements.txt   # Python依存関係
├── run_command.txt    # コピペ用コマンド集
├── README.md          # このファイル
└── spec.md           # 仕様書
```

## 開発者向け情報

### クラス構成

- `KibelaTOCGenerator`: メインクラス
  - `extract_note_id_from_url()`: URLからノートIDを抽出
  - `get_note_content()`: Kibela APIからノート内容を取得
  - `update_note_content()`: Kibela APIでノート内容を更新
  - `extract_headings()`: マークダウンから見出しを抽出
  - `generate_toc()`: 目次のマークダウンを生成
  - `find_existing_toc()`: 既存の目次を検索
  - `insert_or_update_toc()`: 目次の挿入または更新

### API仕様

Kibela API v1を使用：
- `GET /api/v1/notes/{id}`: ノート内容の取得
- `PATCH /api/v1/notes/{id}`: ノート内容の更新

## ライセンス

このツールはMITライセンスの下で提供されています。

## 貢献

バグ報告や機能要望は、GitHubのIssueでお知らせください。

## 更新履歴

- v1.0.0: 初回リリース
  - 基本的な目次生成機能
  - 深度指定機能
  - ドライランモード
  - 既存目次の更新機能

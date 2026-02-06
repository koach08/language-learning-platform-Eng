# Google OAuth 設定ガイド

Supabase で Google ログインを有効にするための手順書です。
所要時間: 約15分

---

## 概要

```
Google Cloud Console          Supabase
      │                          │
      ├── OAuth同意画面作成        │
      ├── 認証情報作成 ──────────→ Client ID/Secret を登録
      │                          │
      └── リダイレクトURI登録 ←──── Callback URL を取得
```

---

## Step 1: Google Cloud Console にアクセス

1. https://console.cloud.google.com/ を開く
2. 大学の Google アカウントでログイン（または個人アカウント）

---

## Step 2: プロジェクト作成（または既存を選択）

1. 上部のプロジェクト選択ドロップダウンをクリック
2. 「新しいプロジェクト」をクリック
3. プロジェクト名: `english-learning-platform`（任意）
4. 「作成」をクリック
5. 作成したプロジェクトを選択

---

## Step 3: OAuth 同意画面の設定

1. 左メニュー → 「APIとサービス」 → 「OAuth 同意画面」
2. User Type を選択:
   - **内部**（大学 Google Workspace の場合）: 大学アカウントのみ使用可能
   - **外部**: 誰でも使用可能（本番用）
   → まずは「外部」を選んでテスト
3. 「作成」をクリック

### OAuth 同意画面の入力

| 項目 | 入力内容 |
|------|---------|
| アプリ名 | English Learning Platform |
| ユーザーサポートメール | あなたのメールアドレス |
| アプリのロゴ | （省略可） |
| アプリのホームページ | （省略可、後で設定） |
| デベロッパーの連絡先メール | あなたのメールアドレス |

4. 「保存して次へ」

### スコープの設定

1. 「スコープを追加または削除」をクリック
2. 以下を選択:
   - `email` - メールアドレスの参照
   - `profile` - 基本プロフィール情報
   - `openid` - OpenID Connect
3. 「更新」→「保存して次へ」

### テストユーザー（外部の場合）

1. 「+ ADD USERS」をクリック
2. テストに使うメールアドレスを追加（自分のアドレス）
3. 「保存して次へ」

### 概要

1. 内容を確認して「ダッシュボードに戻る」

---

## Step 4: 認証情報の作成

1. 左メニュー → 「APIとサービス」 → 「認証情報」
2. 上部の「+ 認証情報を作成」→「OAuth クライアント ID」
3. アプリケーションの種類: **ウェブ アプリケーション**
4. 名前: `English Platform Web Client`

### 承認済みの JavaScript 生成元

（今は空でOK、本番時に追加）

### 承認済みのリダイレクト URI ★重要

ここに Supabase の Callback URL を入力します。

1. **別タブで Supabase を開く**
2. プロジェクト → Authentication → Providers → Google
3. 「Callback URL (for OAuth)」をコピー
   - 形式: `https://xxxxx.supabase.co/auth/v1/callback`
4. Google Cloud に戻り、「+ URI を追加」
5. コピーした URL を貼り付け

例:
```
https://abcdefghijk.supabase.co/auth/v1/callback
```

6. 「作成」をクリック

### 認証情報をメモ

作成完了後、以下が表示されます:
- **クライアント ID**: `xxxxx.apps.googleusercontent.com`
- **クライアント シークレット**: `GOCSPX-xxxxx`

**両方をコピーしてメモしておく！**

---

## Step 5: Supabase に認証情報を登録

1. Supabase Dashboard → Authentication → Providers
2. 「Google」の行をクリック
3. 「Enable Sign in with Google」を ON
4. 以下を入力:

| 項目 | 入力 |
|------|------|
| Client ID | Google からコピーした クライアント ID |
| Client Secret | Google からコピーした クライアント シークレット |

5. 「Save」をクリック

---

## Step 6: 動作確認用の設定

### Supabase の Site URL 設定

1. Supabase → Authentication → URL Configuration
2. Site URL: `http://localhost:8501`（ローカル開発用）
3. Redirect URLs に追加:
   - `http://localhost:8501`
   - `http://localhost:8501/`

本番デプロイ時に Streamlit Cloud の URL を追加します。

---

## 完了チェックリスト

- [ ] Google Cloud でプロジェクト作成
- [ ] OAuth 同意画面を設定
- [ ] 認証情報（OAuth クライアント ID）を作成
- [ ] リダイレクト URI に Supabase Callback URL を登録
- [ ] Supabase で Google Provider を有効化
- [ ] Client ID / Secret を Supabase に登録
- [ ] Site URL を localhost:8501 に設定

---

## トラブルシューティング

### 「redirect_uri_mismatch」エラー

→ Google Cloud の「承認済みのリダイレクト URI」と Supabase の Callback URL が完全一致しているか確認

### 「Access blocked: This app's request is invalid」

→ OAuth 同意画面の設定が完了していない可能性。スコープの設定を確認

### ログイン後に 404 エラー

→ Supabase の Site URL / Redirect URLs の設定を確認

---

## 次のステップ

この設定が完了したら、以下の情報を secrets.toml に入力します:
- Supabase Project URL
- Supabase anon key
- （Google の情報は Supabase 側で管理されるので secrets.toml には不要）

secrets.toml の作成手順は次のファイルで説明します。

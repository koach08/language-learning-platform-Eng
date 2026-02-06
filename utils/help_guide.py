import streamlit as st


def show_help_page(user):
    """ヘルプ・使い方ガイド"""
    
    user_name = user.get('name', '')
    
    st.markdown("## 📘 使い方ガイド / User Guide")
    
    if st.button("← ホームに戻る"):
        st.session_state['current_view'] = 'student_home'
        st.rerun()
    
    st.markdown("---")
    
    # 言語切り替え
    lang = st.radio(
        "言語 / Language",
        ["日本語", "English", "両方 / Both"],
        horizontal=True,
        key="help_lang"
    )
    
    show_ja = lang in ["日本語", "両方 / Both"]
    show_en = lang in ["English", "両方 / Both"]
    
    st.markdown("---")
    
    # ===== はじめに =====
    with st.expander("🎯 はじめに / Getting Started", expanded=True):
        if show_ja:
            st.markdown("""
#### はじめに

このプラットフォームは、英語の4技能（話す・書く・読む・聞く）＋語彙を総合的に学習するためのシステムです。

**基本的な流れ：**
1. ログイン後、**ホーム画面**が表示されます
2. 左のメニュー（サイドバー）から学習モジュールを選びます
3. 各モジュールで練習し、スコアやフィードバックを受け取ります
4. 課題がある場合は、締切までに提出してください
5. 学習を続けるとXP（経験値）が貯まり、レベルアップします

**困ったときは：**
- このガイドの該当セクションを確認してください
- 質問掲示板（💬メッセージ → 質問掲示板）で質問できます
- それでも解決しない場合は、先生に直接相談してください
""")
        if show_en:
            st.markdown("""
#### Getting Started

This platform is a comprehensive English learning system covering all four skills (Speaking, Writing, Reading, Listening) plus Vocabulary.

**Basic Flow:**
1. After logging in, you'll see the **Home Dashboard**
2. Select a learning module from the left menu (sidebar)
3. Practice in each module and receive scores and feedback
4. If there are assignments, submit them before the deadline
5. As you study, you earn XP (experience points) and level up

**If you need help:**
- Check the relevant section in this guide
- Post a question on the Question Board (💬 Messages → Question Board)
- If you still need help, contact your teacher directly
""")
    
    # ===== ホーム画面 =====
    with st.expander("🏠 ホーム画面 / Home Dashboard"):
        if show_ja:
            st.markdown("""
#### ホーム画面の見方

ホーム画面には以下の情報が表示されます：

- **学習ステータスバー**: レベル、XP、連続学習日数、CEFRレベル
- **学習状況**: 総学習時間、平均スコア、連続学習日数
- **授業外学習**: 授業以外で行った学習の記録
- **今日のおすすめ**: AIがおすすめする今日の練習
- **学習モジュール**: 各スキルの練習に進むボタン
- **今週のチャレンジ**: 週ごとの目標（達成するとXPボーナス）
- **課題**: 提出が必要な課題の一覧
""")
        if show_en:
            st.markdown("""
#### Understanding the Home Dashboard

The Home Dashboard shows:

- **Status Bar**: Your level, XP, study streak, and CEFR level
- **Learning Summary**: Total study time, average score, streak
- **Extracurricular Learning**: Log learning activities outside class
- **Today's Recommendations**: AI-suggested practice for today
- **Learning Modules**: Buttons to access each skill area
- **Weekly Challenges**: Weekly goals (earn bonus XP when completed)
- **Assignments**: List of assignments with deadlines
""")
    
    # ===== Speaking =====
    with st.expander("🗣️ Speaking（スピーキング）"):
        if show_ja:
            st.markdown("""
#### スピーキング練習の使い方

**音読練習：**
1. テキストが表示されます
2. 「🔊 読み上げ」ボタンでお手本の音声を聞けます
3. 「🎤 録音開始」をタップして、テキストを声に出して読みます
4. 録音が終わったら「⏹️ 停止」をタップ
5. AIが発音・流暢さ・正確さを評価します

**スピーチ練習：**
- トピックを選んで自由にスピーチ
- AIがフィードバックを提供

**会話練習：**
- AIとの英語会話
- 自然な表現を練習できます

**課題提出：**
1. 「📤 課題提出」タブを選択
2. 提出したい課題を選択
3. 音声を録音またはアップロード
4. 「提出」ボタンを押す

**ヒント：**
- 静かな場所で練習しましょう
- お手本の音声を何度も聞いてから録音すると効果的です
- 速さよりも正確さを意識しましょう
""")
        if show_en:
            st.markdown("""
#### How to Use Speaking Practice

**Read Aloud:**
1. A text will be displayed
2. Tap "🔊 Read Aloud" to hear the model pronunciation
3. Tap "🎤 Start Recording" and read the text aloud
4. Tap "⏹️ Stop" when finished
5. AI evaluates your pronunciation, fluency, and accuracy

**Speech Practice:**
- Choose a topic and speak freely
- AI provides feedback

**Conversation Practice:**
- Practice English conversation with AI
- Learn natural expressions

**Assignment Submission:**
1. Select the "📤 Assignment" tab
2. Choose the assignment
3. Record or upload your audio
4. Press "Submit"

**Tips:**
- Practice in a quiet place
- Listen to the model audio several times before recording
- Focus on accuracy rather than speed
""")
    
    # ===== Writing =====
    with st.expander("✍️ Writing（ライティング）"):
        if show_ja:
            st.markdown("""
#### ライティング練習の使い方

1. 課題のトピックを確認します
2. テキストエリアにエッセイ・文章を入力します
3. 「提出」ボタンを押すとAIが添削します
4. フィードバック（文法、表現、構成）を確認します
5. フィードバックをもとに書き直すと効果的です

**ヒント：**
- まずはアウトラインを考えてから書き始めましょう
- Introduction → Body → Conclusion の構成を意識
- 辞書機能（サイドバー）を活用して語彙を増やしましょう
""")
        if show_en:
            st.markdown("""
#### How to Use Writing Practice

1. Check the assignment topic
2. Type your essay in the text area
3. Press "Submit" for AI correction
4. Review feedback (grammar, expression, structure)
5. Rewrite based on feedback for better learning

**Tips:**
- Plan an outline before you start writing
- Follow the Introduction → Body → Conclusion structure
- Use the dictionary (sidebar) to expand your vocabulary
""")
    
    # ===== Reading =====
    with st.expander("📖 Reading（リーディング）"):
        if show_ja:
            st.markdown("""
#### リーディング練習の使い方

1. 記事やテキストを選択します
2. タイマーが自動で読解速度（WPM）を計測します
3. 読み終わったら「読了」ボタンを押します
4. 理解度クイズに答えます
5. スコアとWPMが記録されます

**辞書機能：**
- わからない単語があれば、左のサイドバーの「🔍 辞書」で調べられます
- 調べた単語は「📝 単語帳に追加」で保存できます
- 保存した単語は「マイ単語帳」で復習できます

**🔊 読み上げ機能：**
- 「🔊 読み上げ」ボタンでテキストを音声で聞けます
- 速度調整スライダーで速さを変更できます

**ヒント：**
- まずは全体を通して読み、大意をつかみましょう
- 2回目で細部に注目して読みましょう
- わからない単語は文脈から意味を推測してみてください
""")
        if show_en:
            st.markdown("""
#### How to Use Reading Practice

1. Select an article or text
2. A timer automatically measures your reading speed (WPM)
3. Press "Finished" when you're done reading
4. Answer comprehension quiz questions
5. Your score and WPM are recorded

**Dictionary:**
- Look up unknown words using "🔍 Dictionary" in the sidebar
- Save words with "📝 Add to Word Book"
- Review saved words in "My Word Book"

**🔊 Text-to-Speech:**
- Press "🔊 Read Aloud" to hear the text
- Adjust speed with the slider

**Tips:**
- Read through the entire text first for the main idea
- Read again focusing on details
- Try to guess unknown word meanings from context
""")
    
    # ===== Listening =====
    with st.expander("🎧 Listening（リスニング）"):
        if show_ja:
            st.markdown("""
#### リスニング練習の使い方

1. 音声素材を選択します
2. 音声を聞きます（何度でも再生可能）
3. 理解度チェックの問題に答えます
4. ディクテーション（書き取り）の練習もあります

**ヒント：**
- 1回目は全体の流れを聞きましょう
- 2回目で詳細を聞き取りましょう
- 聞き取れない部分は何度も繰り返して聞きましょう
- スクリプトがある場合は、最後に確認しましょう
""")
        if show_en:
            st.markdown("""
#### How to Use Listening Practice

1. Select audio material
2. Listen to the audio (you can replay as many times as you need)
3. Answer comprehension check questions
4. Dictation (write what you hear) practice is also available

**Tips:**
- First listen for the overall flow
- Second listen for details
- Replay sections you can't catch
- Check the script at the end if available
""")
    
    # ===== Vocabulary =====
    with st.expander("📚 Vocabulary（語彙）"):
        if show_ja:
            st.markdown("""
#### 語彙学習の使い方

**フラッシュカード：**
- 単語カードをめくって学習
- 知っている/知らないで仕分け

**クイズ：**
- 4択クイズで理解度チェック
- タイピングクイズで綴りも練習

**マイ単語帳（📖）：**
- リーディングや辞書で追加した単語を復習
- SRS（間隔反復）で最適なタイミングで復習
- 3つのモード：フラッシュカード、4択、タイピング

**ヒント：**
- 新しい単語は例文と一緒に覚えましょう
- 毎日少しずつ復習すると効果的です
- 単語帳の「復習が必要」な単語を優先しましょう
""")
        if show_en:
            st.markdown("""
#### How to Use Vocabulary Practice

**Flash Cards:**
- Flip through word cards
- Sort by "know" / "don't know"

**Quizzes:**
- Multiple choice quiz for comprehension
- Typing quiz for spelling practice

**My Word Book (📖):**
- Review words added from Reading or Dictionary
- SRS (Spaced Repetition) reviews at optimal timing
- 3 modes: Flash Cards, Multiple Choice, Typing

**Tips:**
- Learn new words together with example sentences
- Review a little bit every day for best results
- Prioritize "due for review" words in your word book
""")
    
    # ===== ゲーミフィケーション =====
    with st.expander("🎮 XP・レベル・バッジ"):
        if show_ja:
            st.markdown("""
#### XP・レベル・バッジについて

**XP（経験値）：**
- 学習するたびにXPが貯まります
- 例：音読練習 25XP、課題提出 40XP、クイズ満点 50XP
- XPが一定値に達するとレベルアップします

**レベル：**
- Lv.1 🌱 Beginner → Lv.10 🌟 Legend
- レベルが上がると新しい称号がもらえます

**ストリーク（連続学習）：**
- 毎日ログインして学習すると🔥ストリークが増えます
- 7日連続で50XPボーナス、30日連続で200XPボーナス！

**バッジ：**
- 特定の条件を達成するとバッジがもらえます
- 例：「初めてのスピーキング」「10記事読了」「7日連続学習」
- ホーム画面の「学習ステータス詳細」で確認できます

**週間チャレンジ：**
- 毎週3つのチャレンジが自動で設定されます
- 達成するとボーナスXPがもらえます
""")
        if show_en:
            st.markdown("""
#### About XP, Levels & Badges

**XP (Experience Points):**
- Earn XP every time you study
- Examples: Read aloud 25XP, Submit assignment 40XP, Perfect quiz 50XP
- Level up when you reach enough XP

**Levels:**
- Lv.1 🌱 Beginner → Lv.10 🌟 Legend
- Earn new titles as you level up

**Streaks:**
- Log in and study every day to build your 🔥 streak
- 7-day streak: 50XP bonus! 30-day streak: 200XP bonus!

**Badges:**
- Earn badges by completing special achievements
- Examples: "First Speaking", "10 Articles Read", "7-Day Streak"
- Check in "Full Status" on the Home screen

**Weekly Challenges:**
- 3 challenges are automatically set each week
- Complete them for bonus XP
""")
    
    # ===== 辞書・単語帳 =====
    with st.expander("📖 辞書・単語帳・発音ヘルパー"):
        if show_ja:
            st.markdown("""
#### 辞書機能

**サイドバーの辞書（🔍）：**
- どの画面からでもアクセスできます
- 英単語を入力すると、意味・発音記号・例文が表示されます
- 「単語帳に追加」で保存できます

**マイ単語帳（📖）：**
- サイドバーの「📖 マイ単語帳」からアクセス
- 3つのタブ：復習(SRS)、単語帳一覧、辞書検索
- SRS（間隔反復）が忘却曲線に基づいて最適なタイミングで復習を提案

**発音ヘルパー（🔊）：**
- サイドバーの「🔊 発音ヘルパー」からアクセス
- 単語の発音記号を調べられます
- 日本人が苦手な音（th, l/r, f/hなど）の練習ガイド
""")
        if show_en:
            st.markdown("""
#### Dictionary & Word Book

**Sidebar Dictionary (🔍):**
- Accessible from any screen
- Enter an English word to see meaning, phonetics, and examples
- Save to your word book with "Add to Word Book"

**My Word Book (📖):**
- Access from "📖 My Word Book" in the sidebar
- 3 tabs: Review (SRS), Word List, Dictionary Search
- SRS (Spaced Repetition) suggests optimal review timing based on the forgetting curve

**Pronunciation Helper (🔊):**
- Access from "🔊 Pronunciation Helper" in the sidebar
- Look up phonetic transcriptions
- Practice guide for sounds difficult for Japanese speakers (th, l/r, f/h, etc.)
""")
    
    # ===== 音声読み上げツール =====
    with st.expander("🔊 音声読み上げをもっと自然にするには / Better Text-to-Speech"):
        if show_ja:
            st.markdown("""
#### 音声読み上げについて

このプラットフォームの音声読み上げ機能は、Edge TTS（Microsoft Neural Voices）を使用しています。
十分に自然な音声ですが、さらに高品質な音声で学習したい場合は、以下の外部ツールの併用をおすすめします。

※ プラットフォーム内蔵の音声が使えない場合は、OpenAI TTS → ブラウザ内蔵音声の順にフォールバックします。

---

**🌐 ブラウザ拡張機能（Chrome / Edge）:**

1. **Read Aloud: テキスト読み上げ音声リーダー**（無料）
   - Chrome/Edgeで使える高品質な読み上げ拡張機能
   - 多数の自然な音声から選べます
""")
            st.link_button(
                "📥 Read Aloud をインストール（Chrome Web Store）",
                "https://chromewebstore.google.com/detail/read-aloud-a-text-to-spee/hdhinadidafjejdhmfkjgnolgimiaplp",
            )
            st.markdown("""
2. **NaturalReader**（無料プランあり）
   - テキストを自然な声で読み上げるツール
   - ブラウザ拡張版・ウェブ版・アプリ版あり
""")
            st.link_button(
                "📥 NaturalReader 公式サイト",
                "https://www.naturalreaders.com/",
            )
            st.markdown("""
---

**🖥️ Windows ユーザー向け: Microsoft Edge の読み上げ機能**

Microsoft Edge ブラウザには高品質な読み上げ機能が標準搭載されています。

**使い方:**
1. Microsoft Edge でページを開く
2. アドレスバーの右側にある **「🔊 音声で読み上げる」** アイコンをクリック（または `Ctrl + Shift + U`）
3. 「音声オプション」で好みの音声と速度を選択

※ Edge の Neural Voice は非常に自然で、英語学習に最適です。
""")
            st.link_button(
                "📖 Edge 読み上げ機能の詳しい使い方（Microsoft公式）",
                "https://support.microsoft.com/ja-jp/topic/read-aloud-reader-%E3%81%A7%E3%83%86%E3%82%AD%E3%82%B9%E3%83%88%E3%82%92%E8%AA%AD%E3%81%BF%E4%B8%8A%E3%81%92%E3%82%8B-459e7a32-3e8e-4959-ab4c-1f8b3e7b10bc",
            )
            st.markdown("""
---

**📱 スマートフォン:**
- **iOS:** 設定 → アクセシビリティ → 読み上げコンテンツ → 「選択項目の読み上げ」をON
- **Android:** 設定 → ユーザー補助 → テキスト読み上げ → Google テキスト読み上げ
""")
        
        if show_en:
            st.markdown("""
#### About Text-to-Speech

This platform uses Edge TTS (Microsoft Neural Voices) for audio playback.
While the built-in voices are quite natural, you can use external tools for even higher quality.

*Note: If Edge TTS is unavailable, the system falls back to OpenAI TTS, then to browser built-in speech.*

---

**🌐 Browser Extensions (Chrome / Edge):**

1. **Read Aloud: A Text to Speech Voice Reader** (Free)
   - High-quality text-to-speech extension for Chrome/Edge
   - Choose from many natural-sounding voices
""")
            if not show_ja:
                st.link_button(
                    "📥 Install Read Aloud (Chrome Web Store)",
                    "https://chromewebstore.google.com/detail/read-aloud-a-text-to-spee/hdhinadidafjejdhmfkjgnolgimiaplp",
                )
            st.markdown("""
2. **NaturalReader** (Free plan available)
   - Natural voice text-to-speech tool
   - Available as browser extension, web app, and mobile app
""")
            if not show_ja:
                st.link_button(
                    "📥 NaturalReader Official Site",
                    "https://www.naturalreaders.com/",
                )
            st.markdown("""
---

**🖥️ For Windows Users: Microsoft Edge Read Aloud**

Microsoft Edge has a built-in high-quality read aloud feature.

**How to use:**
1. Open any page in Microsoft Edge
2. Click the **"🔊 Read Aloud"** icon in the address bar (or press `Ctrl + Shift + U`)
3. Click "Voice options" to choose your preferred voice and speed

*Edge's Neural Voices are extremely natural and ideal for English learning.*
""")
            if not show_ja:
                st.link_button(
                    "📖 How to use Edge Read Aloud (Microsoft Support)",
                    "https://support.microsoft.com/en-us/topic/use-read-aloud-in-reader-459e7a32-3e8e-4959-ab4c-1f8b3e7b10bc",
                )
            st.markdown("""
---

**📱 Smartphones:**
- **iOS:** Settings → Accessibility → Spoken Content → Turn on "Speak Selection"
- **Android:** Settings → Accessibility → Text-to-speech → Google Text-to-speech
""")
    
    # ===== メッセージ =====
    with st.expander("💬 メッセージ・質問掲示板"):
        if show_ja:
            st.markdown("""
#### メッセージ機能

**お知らせ（📢）：**
- 先生からのお知らせが表示されます
- 重要なお知らせは🔴マークがつきます

**メッセージ（📩）：**
- 先生にメッセージを送れます
- 件名と本文を入力して送信

**質問掲示板（❓）：**
- クラスメイトと共有できる質問掲示板
- 質問を投稿すると、先生やクラスメイトが回答できます
- タグ機能で質問をカテゴリ分けできます
- 役に立つ質問には👍を押しましょう
""")
        if show_en:
            st.markdown("""
#### Messaging Features

**Announcements (📢):**
- See announcements from your teacher
- Important ones are marked with 🔴

**Messages (📩):**
- Send messages to your teacher
- Enter subject and body, then send

**Question Board (❓):**
- A shared board where you can post questions
- Teachers and classmates can reply
- Use tags to categorize questions
- Upvote 👍 helpful questions
""")
    
    # ===== 授業外学習 =====
    with st.expander("📝 授業外学習ログ"):
        if show_ja:
            st.markdown("""
#### 授業外学習の記録

授業以外で行った英語学習を記録して、ポイントを獲得できます。

**記録できるもの：**
- 映画・ドラマ鑑賞（英語字幕あり）
- 英語の本・記事を読んだ
- 英語のポッドキャスト・音楽
- 英語アプリでの学習
- 外国人との会話
- その他の英語学習

**記録の方法：**
1. ホーム画面の「📝 記録する」をタップ
2. カテゴリ、タイトル、学習時間を入力
3. 「記録」ボタンで保存
4. ポイントが自動で計算されます
""")
        if show_en:
            st.markdown("""
#### Extracurricular Learning Log

Record English learning activities outside of class and earn points.

**What you can log:**
- Watching movies/dramas (with English subtitles)
- Reading English books/articles
- English podcasts/music
- Language learning apps
- Conversations with English speakers
- Other English study activities

**How to log:**
1. Tap "📝 Record" on the Home screen
2. Enter category, title, and study time
3. Press "Record" to save
4. Points are calculated automatically
""")
    
    # ===== トラブルシューティング =====
    with st.expander("🔧 トラブルシューティング / Troubleshooting"):
        if show_ja:
            st.markdown("""
#### よくある問題と解決法

**Q: ログインできない**
- メールアドレスが正しいか確認してください
- クラスコードが正しいか確認してください
- それでもダメな場合は先生に連絡してください

**Q: 録音ができない**
- ブラウザのマイク許可を確認してください
- Chrome / Safari の最新版を使用してください
- イヤホンマイクを使うと認識精度が上がります

**Q: 音声が再生されない**
- デバイスの音量を確認してください
- ブラウザの音声自動再生が許可されているか確認
- 別のブラウザで試してみてください

**Q: ページが正しく表示されない**
- ブラウザを更新（リロード）してください
- キャッシュをクリアしてみてください
- Chrome / Safari / Firefox の最新版をお使いください

**Q: 課題の提出方法がわからない**
- 各モジュール（Speaking等）の「📤 課題提出」タブから提出
- 締切前に必ず提出してください
- 提出後は「提出済み」と表示されます

**Q: スコアが低い / 評価がおかしい**
- AI評価は参考値です。最終評価は先生が行います
- 静かな環境で録音すると精度が上がります
- 何度も練習してからベストな録音を提出しましょう
""")
        if show_en:
            st.markdown("""
#### Common Problems & Solutions

**Q: I can't log in**
- Check that your email address is correct
- Verify your class code
- Contact your teacher if problems persist

**Q: Recording doesn't work**
- Check microphone permissions in your browser
- Use the latest version of Chrome / Safari
- Using earphone microphone improves recognition

**Q: Audio won't play**
- Check your device volume
- Make sure auto-play is enabled in your browser
- Try a different browser

**Q: Page doesn't display correctly**
- Refresh/reload the browser
- Clear your browser cache
- Use the latest Chrome / Safari / Firefox

**Q: I don't know how to submit assignments**
- Submit from the "📤 Assignment" tab in each module
- Make sure to submit before the deadline
- After submission, it will show "Submitted"

**Q: My score is low / evaluation seems wrong**
- AI evaluation is for reference. Final grades are given by your teacher
- Recording in a quiet environment improves accuracy
- Practice multiple times and submit your best recording
""")
    
    # ===== 先生に相談 =====
    st.markdown("---")
    st.markdown("### 🆘 それでも解決しない場合 / Still Need Help?")
    
    col1, col2 = st.columns(2)
    with col1:
        if show_ja:
            st.info("""
**先生に相談する方法：**
1. 💬 メッセージ機能で先生に直接メッセージを送る
2. ❓ 質問掲示板に質問を投稿する
3. 授業中に直接質問する

※ 技術的な問題（ログインできない等）は、
メールまたは授業前後に直接相談してください。
""")
    with col2:
        if show_en:
            st.info("""
**How to contact your teacher:**
1. 💬 Send a direct message through Messages
2. ❓ Post on the Question Board
3. Ask during class

※ For technical issues (can't log in, etc.),
email your teacher or ask before/after class.
""")
    
    if st.button("💬 先生にメッセージを送る / Send a Message to Your Teacher", type="primary", use_container_width=True):
        st.session_state['current_view'] = 'messaging'
        st.rerun()

#!/bin/bash
# callback.html を配信する簡易HTTPサーバー (ポート8502)
python3 -m http.server 8502 --directory static &
CALLBACK_PID=$!

# Streamlit起動
streamlit run app.py

# 終了時にHTTPサーバーも停止
kill $CALLBACK_PID

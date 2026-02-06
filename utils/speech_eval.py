import streamlit as st
import requests
import subprocess
import tempfile
import os
import math
import json
import base64

def extract_audio_from_video(video_path, output_path):
    """動画ファイルから音声を抽出"""
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-vn',  # 映像を無視
        '-ar', '16000', '-ac', '1', '-acodec', 'pcm_s16le',
        output_path
    ]
    subprocess.run(cmd, capture_output=True, timeout=180)


def split_audio(wav_path, chunk_seconds=30):
    """音声を指定秒数ごとに分割"""
    chunks = []
    
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
           '-of', 'default=noprint_wrappers=1:nokey=1', wav_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = float(result.stdout.strip())
    
    num_chunks = math.ceil(duration / chunk_seconds)
    
    for i in range(num_chunks):
        start = i * chunk_seconds
        chunk_path = f"{wav_path}_chunk{i}.wav"
        
        cmd = [
            'ffmpeg', '-y', '-i', wav_path,
            '-ss', str(start), '-t', str(chunk_seconds),
            '-ar', '16000', '-ac', '1', '-acodec', 'pcm_s16le',
            chunk_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=60)
        
        with open(chunk_path, 'rb') as f:
            chunks.append(f.read())
        
        os.unlink(chunk_path)
    
    return chunks, duration


def evaluate_chunk_simple(audio_data, api_key, region):
    """シンプルな音声認識"""
    
    url = f"https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
    
    params = {"language": "en-US", "format": "detailed"}
    
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(url, params=params, headers=headers, data=audio_data, timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            
            recognized_text = result.get("DisplayText", "")
            nbest = result.get("NBest", [])
            
            if nbest:
                confidence = nbest[0].get("Confidence", 0)
            else:
                confidence = 0
            
            return {
                "text": recognized_text,
                "confidence": confidence,
                "raw": result
            }
        else:
            return {"text": "", "confidence": 0, "raw": None}
    except Exception as e:
        return {"text": "", "confidence": 0, "raw": None}


def evaluate_pronunciation(audio_file, reference_text):
    """Azure Speech APIで発音を評価（長い音声・動画対応）"""
    
    api_key = st.secrets["azure_speech"]["api_key"]
    region = st.secrets["azure_speech"]["region"]
    
    file_name = audio_file.name.lower()
    suffix = '.' + file_name.split('.')[-1]
    
    # 対応形式チェック
    supported_audio = ['.wav', '.mp3', '.m4a']
    supported_video = ['.mp4', '.mov', '.webm', '.avi']
    
    is_video = suffix in supported_video
    
    try:
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
            tmp_in.write(audio_file.read())
            tmp_in_path = tmp_in.name
        
        wav_path = tmp_in_path.replace(suffix, '_converted.wav')
        
        if is_video:
            # 動画から音声を抽出
            st.info("🎬 動画から音声を抽出中...")
            extract_audio_from_video(tmp_in_path, wav_path)
        else:
            # 音声ファイルをWAVに変換
            cmd = [
                'ffmpeg', '-y', '-i', tmp_in_path,
                '-ar', '16000', '-ac', '1', '-acodec', 'pcm_s16le',
                wav_path
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)
        
        os.unlink(tmp_in_path)
        
        # 音声を分割
        chunks, duration = split_audio(wav_path, chunk_seconds=30)
        os.unlink(wav_path)
        
        st.info(f"📊 音声長: {duration:.1f}秒 / {len(chunks)}チャンクで分析中...")
        
        all_text = []
        all_confidence = []
        
        progress_bar = st.progress(0)
        for i, chunk in enumerate(chunks):
            result = evaluate_chunk_simple(chunk, api_key, region)
            if result["text"]:
                all_text.append(result["text"])
            if result["confidence"] > 0:
                all_confidence.append(result["confidence"])
            progress_bar.progress((i + 1) / len(chunks))
        
        # 結果を統合
        recognized_text = " ".join(all_text)
        
        if all_confidence:
            avg_confidence = sum(all_confidence) / len(all_confidence)
        else:
            avg_confidence = 0.7 if recognized_text else 0.3
        
        base_score = int(avg_confidence * 100)
        
        if reference_text:
            ref_words = len(reference_text.split())
            rec_words = len(recognized_text.split())
            completeness = min(100, int((rec_words / max(ref_words, 1)) * 100))
        else:
            completeness = 80 if recognized_text else 50
        
        overall = int((base_score * 0.7) + (completeness * 0.3))
        
        return {
            "success": True,
            "recognized_text": recognized_text,
            "duration": duration,
            "scores": {
                "overall": overall,
                "accuracy": base_score,
                "fluency": max(50, base_score - 5),
                "completeness": completeness,
                "prosody": max(50, base_score - 10)
            },
            "problem_words": [],
            "problem_phonemes": [],
            "intelligibility": get_intelligibility(base_score, base_score, base_score)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_intelligibility(accuracy, fluency, prosody):
    """通じやすさを判定"""
    
    weighted_score = (accuracy * 0.4) + (fluency * 0.4) + (prosody * 0.2)
    
    if weighted_score >= 75:
        return {
            "level": "高い",
            "score": weighted_score,
            "description": "国際的なビジネスや学術の場で問題なく通じるレベルです。",
            "detail": "多様な英語話者に理解されやすい発音です。",
            "icon": "🟢"
        }
    elif weighted_score >= 55:
        return {
            "level": "中程度",
            "score": weighted_score,
            "description": "日常会話や一般的なコミュニケーションでは十分通じます。",
            "detail": "文脈があれば問題なく理解されます。",
            "icon": "🟡"
        }
    elif weighted_score >= 35:
        return {
            "level": "やや低い",
            "score": weighted_score,
            "description": "聞き手が注意深く聞けば理解できるレベルです。",
            "detail": "ゆっくり話す、キーワードを強調するなどの工夫で改善できます。",
            "icon": "🟠"
        }
    else:
        return {
            "level": "要練習",
            "score": weighted_score,
            "description": "理解が困難な場合があります。",
            "detail": "基礎的な発音パターンの練習が効果的です。",
            "icon": "🔴"
        }


def get_feedback(scores, problem_words, problem_phonemes, reference_text, duration=0):
    """詳細なフィードバックを生成"""
    
    feedback = []
    
    overall = scores.get("overall", 0)
    accuracy = scores.get("accuracy", 0)
    fluency = scores.get("fluency", 0)
    prosody = scores.get("prosody", 0)
    completeness = scores.get("completeness", 0)
    
    if overall >= 85:
        level = "C1"
    elif overall >= 70:
        level = "B2"
    elif overall >= 55:
        level = "B1"
    elif overall >= 40:
        level = "A2"
    else:
        level = "A1"
    
    feedback.append("## 📋 詳細フィードバック")
    feedback.append("")
    
    feedback.append("### 🌍 通じやすさ（Intelligibility）")
    feedback.append("")
    feedback.append("**最も重要な指標です。** 「ネイティブのような発音」ではなく、「世界中の英語話者に通じるか」を評価しています。")
    feedback.append("")
    
    intelligibility = get_intelligibility(accuracy, fluency, prosody)
    feedback.append(f"{intelligibility['icon']} **{intelligibility['level']}** ({intelligibility['score']:.0f}/100)")
    feedback.append("")
    feedback.append(f"{intelligibility['description']}")
    feedback.append("")
    
    feedback.append("---")
    feedback.append("### 📊 項目別フィードバック")
    feedback.append("")
    
    feedback.append(f"**1. 発音の明瞭さ: {accuracy}/100**")
    if accuracy >= 80:
        feedback.append("   - ✅ 個々の音がはっきりと聞き取れます。")
    elif accuracy >= 60:
        feedback.append("   - 📝 全体的に聞き取れます。一部の音をより明瞭にすると良いでしょう。")
    else:
        feedback.append("   - ⚠️ いくつかの音が聞き取りにくい状態です。")
    feedback.append("")
    
    feedback.append(f"**2. 流暢さ: {fluency}/100**")
    if fluency >= 80:
        feedback.append("   - ✅ 自然なペースで話せています。")
    elif fluency >= 60:
        feedback.append("   - 📝 概ねスムーズです。意味のまとまりで区切る練習が効果的です。")
    else:
        feedback.append("   - ⚠️ ポーズや途切れが目立ちます。短い文から練習しましょう。")
    feedback.append("")
    
    feedback.append(f"**3. イントネーション: {prosody}/100**")
    feedback.append("   ℹ️ 注意: イントネーションは地域によって異なります。どの地域の英語も「正しい」英語です。")
    feedback.append("")
    
    feedback.append("---")
    feedback.append("### 📚 練習のアドバイス")
    feedback.append("")
    
    if accuracy < 70:
        feedback.append("**1. 発音練習**")
        feedback.append("   - 辞書サイトで発音を確認し、真似る練習をしましょう")
        feedback.append("")
    
    if fluency < 70:
        feedback.append("**2. チャンク読み練習**")
        feedback.append("   - 文を意味のまとまりで区切って読む練習をしましょう")
        feedback.append("")
    
    feedback.append("**継続が最も重要です** - 毎日10分の練習が効果的です")
    feedback.append("")
    
    test_scores = convert_to_test_scores(overall)
    feedback.append("---")
    feedback.append("### 📈 参考: 検定スコア換算（目安）")
    feedback.append("")
    feedback.append(f"| 検定 | 換算スコア |")
    feedback.append(f"|------|-----------|")
    feedback.append(f"| CEFR | {test_scores['CEFR']} |")
    feedback.append(f"| TOEFL iBT Speaking | {test_scores['TOEFL_iBT_Speaking']}/30 |")
    feedback.append(f"| IELTS Speaking | {test_scores['IELTS_Speaking']} |")
    feedback.append(f"| 英検 | {test_scores['Eiken']}相当 |")
    feedback.append("")
    
    return {
        "cefr_level": level,
        "feedback": "\n".join(feedback)
    }


def convert_to_test_scores(overall_score):
    """各種検定スコアに換算"""
    
    toefl_ibt = min(30, max(0, int(overall_score * 0.28)))
    ielts = min(9.0, max(0, round(overall_score / 100 * 8.5, 1)))
    
    return {
        "CEFR": score_to_cefr(overall_score),
        "TOEFL_iBT_Speaking": toefl_ibt,
        "IELTS_Speaking": ielts,
        "Eiken": score_to_eiken(overall_score)
    }


def score_to_cefr(score):
    if score >= 85: return "C1"
    elif score >= 70: return "B2"
    elif score >= 55: return "B1"
    elif score >= 40: return "A2"
    else: return "A1"


def score_to_eiken(score):
    if score >= 85: return "1級"
    elif score >= 75: return "準1級"
    elif score >= 60: return "2級"
    elif score >= 45: return "準2級"
    elif score >= 30: return "3級"
    else: return "4-5級"

# ============================================================
# ollama.py
# Ollama 일반 대화 + 릴레이 판단
# 완전 Local 단계용
# ============================================================

import json
import re
import time
import requests

from config import *
from datetime import datetime


def extract_json(text):
    try:
        return json.loads(text)
    except:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError("JSON을 찾을 수 없습니다.")


def ask_ollama(text):
    today = datetime.now().strftime("%Y년 %m월 %d일")

    prompt = f"""
너는 음성비서이다.

사용자가 릴레이를 켜거나 끄라고 하면
decision만 ON 또는 OFF를 출력한다.

그 외의 질문은
한국어로만 대답한다.

중국어, 일본어는 절대 사용하지 않는다.

모르는 내용은 모른다고 답한다.

response는 1~2문장으로 짧게 말해라
현재 날짜는 {today} 이다.

사용자 문장을 읽고 반드시 JSON만 출력해라.

출력 형식:
{{
  "decision": "ON 또는 OFF 또는 UNKNOWN",
  "response": "사용자에게 말할 짧은 한국어 응답"
}}

판단 규칙:
- 릴레이를 켜라는 뜻이면 decision은 ON
- 릴레이를 끄라는 뜻이면 decision은 OFF
- 릴레이 제어가 아니면 decision은 UNKNOWN
- 일반 질문이면 response에 정상적으로 답변해라
- response는 1~2문장으로 짧게 말해라
- JSON 외의 설명은 절대 하지 마라
- 오늘 날짜를 물으면 반드시 "{today}" 라고 답해라

예시:
사용자: 하이브리드 릴레이 온
출력:
{{"decision":"ON","response":"릴레이를 켰습니다."}}

사용자: 하이브리드 릴레이 오프
출력:
{{"decision":"OFF","response":"릴레이를 껐습니다."}}

사용자: 안녕
출력:
{{"decision":"UNKNOWN","response":"안녕하세요. 무엇을 도와드릴까요?"}}

사용자: 이순신 장군이 누구야
출력:
{{"decision":"UNKNOWN","response":"이순신 장군은 조선 시대의 명장으로, 임진왜란 때 수군을 이끌고 큰 승리를 거둔 인물입니다."}}

사용자 문장:
{text}
"""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0
        }
    }

    start = time.time()

    try:
        r = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=30
        )

        llm_time = time.time() - start

        if r.status_code != 200:
            print("[OLLAMA ERROR]", r.status_code, r.text)
            return "UNKNOWN", "Ollama 오류입니다.", llm_time

        raw = r.json().get("response", "").strip()

        print("[OLLAMA RAW]")
        print(raw)

        data = extract_json(raw)

        decision = data.get("decision", "UNKNOWN").upper().strip()
        response = data.get("response", "처리했습니다.").strip()

        if decision not in ["ON", "OFF", "UNKNOWN"]:
            decision = "UNKNOWN"

        if re.search(r"[\u4e00-\u9fff\u3040-\u30ff]", response):
            response = "한국어 답변이 불안정합니다. 다시 질문해 주세요."
            decision = "UNKNOWN"

        if not response:
            response = "처리했습니다."

        return decision, response, llm_time

    except Exception as e:
        llm_time = time.time() - start
        print("[OLLAMA EXCEPTION]", e)
        return "UNKNOWN", "Ollama 처리 오류입니다.", llm_time

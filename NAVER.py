import os
import json
import httpx
from dotenv import load_dotenv
from prompts import naver_system_prompt
from httpx import ReadTimeout

load_dotenv()

NAVER_URL = os.getenv("NAVER_URL")
NAVER_AUTH = os.getenv("NAVER_BEARER_TOKEN")   # token trong .env


# ======================================================
#   Chuẩn hóa RAG text từ note / internet / file
# ======================================================
async def normalize_rag(note, internet, file_obj) -> str:

    # 1) file upload
    if file_obj and hasattr(file_obj, "read"):
        content = await file_obj.read()
        try:
            return content.decode("utf-8")
        except:
            return content.decode("latin-1", errors="ignore")

    # 2) note text
    if note and str(note).strip():
        return str(note)

    # 3) internet text
    if internet and str(internet).strip():
        return str(internet)

    return ""


# ======================================================
#   Ghép list câu checkworthy → Multi-sentence TEXT
# ======================================================
def build_new_text(checkworthy_list: list[str]) -> str:
    return "\n".join(checkworthy_list)


# ======================================================
#   Build JSON BODY cho API NAVER
# ======================================================
def build_naver_body(new_text: str, rag_text: str):
    return {
        "messages": [
            { "role": "system", "content": naver_system_prompt },
            {
                "role": "user",
                "content": f"NEW TEXT:\n{new_text}\n\nRETRIEVED INFORMATION (RAG):\n{rag_text}"
            }
        ],
        "thinking": {"effort": "high"},
        "topP": 0.8,
        "topK": 0,
        "maxCompletionTokens": 32768,
        "temperature": 0.5,
        "repetitionPenalty": 1.1,
        "seed": 42,
        "includeAiFilters": True
    }


# ======================================================
#   Gọi API NAVER — tối ưu cho FastAPI
# ======================================================

async def call_naver(checkworthy_list: list[str], note=None, internet=None, file=None):
    """
    Input:
    - checkworthy_list: list[str]
    - note / internet: optional text
    - file: UploadFile

    Output:
    - JSON response từ NAVER hoặc lỗi timeout
    """

    # debug
    print("\n=== DEBUG INPUT FROM POSTMAN ===")
    print("checkworthy_list:", checkworthy_list)
    print("note:", note)
    print("internet:", internet)
    print("file:", file)
    print("===============================\n")

    if not NAVER_AUTH:
        raise Exception("NAVER_BEARER_TOKEN không tồn tại trong .env")

    new_text = build_new_text(checkworthy_list)
    rag_text = await normalize_rag(note, internet, file)

    body = build_naver_body(new_text, rag_text)

    headers = {
        "Authorization": NAVER_AUTH,
        "Content-Type": "application/json"
    }

    try:
        # ---- 🔥 SET 5 MINUTES TIMEOUT (300s) ----
        async with httpx.AsyncClient(timeout=300) as client:  
            response = await client.post(NAVER_URL, headers=headers, json=body)

        return response.json()

    except ReadTimeout:
        # ---- 🔥 THROW A NICE JSON ERROR FOR FE ----
        return {
            "error": True,
            "type": "timeout",
            "message": "NAVER AI server took too long to respond (over 5 minutes). Please try again."
        }

    except Exception as e:
        # ---- Nếu lỗi khác (HTTP, JSON, network) ----
        return {
            "error": True,
            "type": "exception",
            "message": str(e)
        }

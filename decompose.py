import json
import asyncio
from prompts import decompose_prompt


async def decompose_text(model, text: str):
    """
    Gọi Gemini để trích xuất atomic claims.
    model: GenerativeModel được truyền từ gemini_client
    text : nội dung cần xử lý
    """

    prompt = decompose_prompt.format(doc=text)

    try:
        # Vì Google SDK không async, ta chạy trong thread pool để không block event loop
        response = await asyncio.to_thread(model.generate_content, prompt)
        raw = response.text.strip()
    except Exception as e:
        return {"error": f"Lỗi gọi Gemini: {e}"}

    # Nếu Gemini trả về block kiểu ```json
    if raw.startswith("```"):
        raw = raw.strip("`").replace("json", "").strip()

    try:
        data = json.loads(raw)
        return {"claims": data.get("claims", [])}
    except Exception:
        return {
            "error": "Gemini trả về output không phải JSON hợp lệ",
            "raw": raw
        }


async def decompose_input(model, text: str):
    """
    Hàm public để gọi trong router FastAPI.
    Nhận text → trả list claims.
    """
    return await decompose_text(model, text)

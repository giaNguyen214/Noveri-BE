import json
import asyncio
from prompts import checkworthy_prompt


async def _call_llm(model, prompt: str):
    """
    Gọi Gemini bằng thread pool vì SDK không async.
    """
    try:
        response = await asyncio.to_thread(
            model.generate_content,
            contents=[prompt],
            generation_config={"temperature": 0}
        )

        txt = response.text
        if not txt:
            return None
        return txt.strip()

    except Exception as e:
        return {"error": f"LLM error: {e}"}


async def identify_checkworthy(model, texts: list[str], num_retries: int = 3):
    """
    Nhận list statements → trả về:
    - danh sách câu checkworthy
    - full mapping JSON
    """

    # Tạo list dạng:
    # 1. text1
    # 2. text2
    # ...
    numbered = "\n".join([f"{i+1}. {t}" for i, t in enumerate(texts)])

    # Format prompt template
    prompt = checkworthy_prompt.format(texts=numbered)

    mapping = {}
    checkworthy_claims = []

    for attempt in range(num_retries):

        raw = await _call_llm(model, prompt)

        if raw is None or isinstance(raw, dict) and raw.get("error"):
            # retry nếu fail
            continue

        cleaned = raw.strip()

        # Remove ```json block
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        # Remove extra labels
        cleaned = (
            cleaned.replace("JSON:", "")
                   .replace("Output:", "")
                   .strip()
        )

        # Parse JSON
        try:
            data = json.loads(cleaned)
            mapping = data

            # Validate Yes/No format
            valid = all(
                v.startswith("Yes") or v.startswith("No")
                for v in data.values()
            )

            if not valid:
                raise ValueError("Invalid mapping values")

            # Extract checkworthy sentences
            checkworthy_claims = [
                k for k, v in data.items()
                if v.startswith("Yes")
            ]

            break  # SUCCESS → stop retry

        except Exception:
            # Retry tiếp nếu lỗi parse
            continue

    return checkworthy_claims, mapping

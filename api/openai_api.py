# api/openai_api.py
import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

def analyze_image_with_gpt(image_path):
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API 키가 .env 파일에 설정되지 않았습니다.")

    client = OpenAI(api_key=api_key)

    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    prompt_text = """
    이 이미지는 영수증 또는 명함입니다. 내용을 분석해서 아래의 JSON 형식 중 하나로 반환해주세요.
    만약 영수증이라면, 상호명(store_name), 총 결제 금액(total_amount), 거래일시(transaction_date)를 추출해주세요.
    만약 명함이라면, 이름(name), 회사(company), 직책(title), 전화번호(phone), 이메일(email)을 추출해주세요.
    해당하는 정보가 없으면 "정보 없음"으로 표기해주세요. 다른 설명 없이 JSON 객체만 반환해야 합니다.

    영수증 형식:
    {
      "type": "receipt",
      "data": {
        "store_name": "상호명",
        "total_amount": "총액",
        "transaction_date": "YYYY-MM-DD"
      }
    }

    명함 형식:
    {
      "type": "business_card",
      "data": {
        "name": "이름",
        "company": "회사명",
        "title": "직책",
        "phone": "전화번호",
        "email": "이메일 주소"
      }
    }
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            max_tokens=500,
        )
        content = response.choices[0].message.content
        # 마크다운 코드 블록 제거
        if content.startswith("```json"):
            content = content[7:-3].strip()
        
        return json.loads(content)
    
    except Exception as e:
        print(f"API 호출 오류: {e}")
        return {"type": "error", "data": {"message": str(e)}}
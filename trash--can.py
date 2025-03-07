import os
import openai
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from PIL import Image
import base64
import json
from dotenv import load_dotenv  # 환경 변수 로드를 위한 dotenv 추가

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정 (.env에서 불러오기)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

# OpenAI 클라이언트 초기화
client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
CORS(app)  # CORS 허용

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def encode_image(image_path):
    """ 이미지 파일을 Base64로 변환 """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

@app.route("/upload", methods=["POST"])
def upload_photo():
    try:
        print(f"📥 요청 파일 목록: {request.files}")

        if not request.files:
            return jsonify({"error": "not exist image"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "no file"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, "photo.jpg")
        with open(file_path, "wb") as f:
            f.write(file.read())

        print(f"📸 이미지 저장 완료: {file_path}")

        # GPT에게 이미지 분석 요청
        question = "이 이미지는 일반쓰레기/플라스틱/캔/병 중에 어떤건지 단답형으로 알려줘?"
        encoded_image = encode_image(file_path)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI that analyzes images."},
                {"role": "user", "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                ]}
            ],
            max_tokens=500
        )

        answer = response.choices[0].message.content
        answer = answer.encode("utf-8").decode("utf-8")
        print(f"🤖 GPT 응답: {answer}")
 
        return Response(json.dumps({"answer": answer}, ensure_ascii=False), content_type="application/json; charset=utf-8")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

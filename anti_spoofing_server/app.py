from flask import Flask, request, jsonify
import os
import base64
import uuid
from src.anti_spoof_predict import predict_image

app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400

        base64_str = data['image']

        # 만약 'data:image/jpeg;base64,' 이런 prefix가 있다면 제거
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]

        # base64 디코딩
        image_data = base64.b64decode(base64_str)

        # 저장할 고유 파일명 생성
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # 이미지 저장
        with open(filepath, 'wb') as f:
            f.write(image_data)

        # 이미지 예측
        result = predict_image(filepath)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'Image processing failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

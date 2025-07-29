# utils/file_handler.py
import os
import shutil
import uuid

def save_uploaded_image(source_path):
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # 고유한 파일명 생성
    file_extension = os.path.splitext(source_path)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    destination_path = os.path.join(uploads_dir, unique_filename)

    shutil.copy(source_path, destination_path)
    return destination_path
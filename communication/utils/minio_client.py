from minio import Minio
from django.conf import settings
from uuid import uuid4
from datetime import datetime, timedelta
from minio.error import S3Error

minio_config = settings.MINIO_STORAGE

client = Minio(
    endpoint=minio_config['ENDPOINT'],
    access_key=minio_config['ACCESS_KEY'],
    secret_key=minio_config['SECRET_KEY'],
    secure=minio_config['SECURE']
)

bucket_name = minio_config['BUCKET_NAME']
_checked_buckets = set()


def ensure_bucket_exists(bucket):
    if bucket in _checked_buckets:
        return
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        _checked_buckets.add(bucket)
    except S3Error as e:
        print(f"MinIO error while checking/creating bucket '{bucket}': {e}")
        raise


def save_file_to_minio(file, user=None, file_type='user_upload', subject_name=None):
    # Проверка на наличие файла
    if file is None:
        raise ValueError("File is not provided or is invalid")

    ensure_bucket_exists(bucket_name)

    # Извлекаем расширение файла, если оно существует
    ext = file.name.split('.')[-1] if '.' in file.name else 'unknown'

    if file_type == 'lecture':
        date_str = datetime.now().strftime('%d.%m.%Y')
        subject = subject_name or 'предмет'
        safe_subject = subject.replace(' ', '_').replace('"', '')
        filename = f"Лекция от {date_str} по \"{safe_subject}\".{ext}"
        path = f"system/lectures/{filename}"
    elif file_type == 'report':
        date_str = datetime.now().strftime('%d.%m.%Y')
        filename = f"Отчёт_активности_{date_str}.{ext}"
        path = f"system/activity_reports/{filename}"
        
    elif file_type == 'transcript':
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"Транскрипт_{date_str}_{uuid4().hex[:6]}.txt"
        path = f"system/transcripts/{filename}"

    else:
        # Генерация уникального имени для файла
        filename = f"{uuid4()}.{ext}"
        path = f"uploads/users/{filename}"

    try:
        client.put_object(
            bucket_name,
            path,
            file,
            length=file.size,
            content_type=file.content_type,
        )
    except S3Error as e:
        print(f"MinIO error while uploading file '{filename}': {e}")
        raise


    # Генерация временной ссылки, живущей 7 дней
    try:
        expires = timedelta(days=7)
        presigned_url = client.presigned_get_object(bucket_name, path, expires=expires, response_headers={
            "response-content-disposition": f'attachment; filename="{file.name}"'
        })
    except S3Error as e:
        print(f"MinIO error while generating presigned URL for '{path}': {e}")
        presigned_url = None

    return {
        "path": path,
        "file_name": file.name,
        "url": presigned_url,
    }

def get_presigned_icon_url(object_path: str, expires_days: int = 1) -> str | None:
    """
    Генерирует presigned URL для объекта иконки в MinIO.
    
    :param object_path: Путь к объекту в бакете (например "online-school/system/icons/Menu_icon_icon-icons.com_71858.png")
    :param expires_days: Время жизни ссылки в днях (по умолчанию 7)
    :return: presigned URL или None, если ошибка
    """
    try:
        expires = timedelta(days=expires_days)
        presigned_url = client.presigned_get_object(bucket_name, object_path, expires=expires)
        return presigned_url
    except S3Error as e:
        print(f"MinIO error while generating presigned URL for '{object_path}': {e}")
        return None
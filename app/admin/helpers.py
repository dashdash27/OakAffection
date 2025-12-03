from app.models import Product
from app.extensions import STATIC_DIR
from app.logger import logger

import os
from slugify import slugify
from werkzeug.utils import secure_filename
from datetime import datetime

def unique_img_name_gen(obj, file_data):
    base_path = os.path.join(STATIC_DIR, 'img', 'uploads')
    filename = secure_filename(file_data.filename)
    name, ext = os.path.splitext(filename)

    counter = 0
    unique_filename = filename
    while os.path.exists(os.path.join(base_path, unique_filename)):
        counter += 1
        unique_filename = f"{name}-{counter}{ext}"
    
    return unique_filename

def unique_video_name_gen(obj, file_data):
    base_path = os.path.join(STATIC_DIR, 'videos', 'uploads')
    filename = secure_filename(file_data.filename)
    name, ext = os.path.splitext(filename)

    counter = 0
    unique_filename = filename
    while os.path.exists(os.path.join(base_path, unique_filename)):
        counter += 1
        unique_filename = f"{name}-{counter}{ext}"
    
    return unique_filename

def unique_color_icon_name_gen(file_data):
    base_path = os.path.join(STATIC_DIR, 'img', 'colors')
    filename = secure_filename(file_data.filename)
    name, ext = os.path.splitext(filename)

    counter = 0
    unique_filename = filename
    while os.path.exists(os.path.join(base_path, unique_filename)):
        counter += 1
        unique_filename = f"{name}-{counter}{ext}"
    
    return unique_filename

def generate_unique_slug(name):
    base_slug = slugify(name)
    slug = base_slug
    counter = 1

    # проверка, если ли такой же slug
    while Product.query.filter_by(slug=slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug

def contains_equal_photo_url(product, photo_url):
    for p in product.photos:
        if p.photo_url == photo_url:
            return True
    return False

def contains_equal_video_url(product, video_url):
    for p in product.videos:
        if p.video_url == video_url:
            return True
    return False

def delete_photo_by_path(photo_url):
    """Удаление фото из файловой системы по photo_path"""
    static_path = STATIC_DIR
    photo_file_path = os.path.normpath(os.path.join(static_path, photo_url))

    try:
        if os.path.exists(photo_file_path):
            os.remove(photo_file_path)
            logger.info(f"--> удалено фото: '{photo_url}'")
        else:
            logger.info(f"--> фото не найдено в ФС: '{photo_url}'")
    except OSError as e:
        logger.error(f"--> ошибка при удалении файла '{photo_url}': {e}")

def delete_video_by_path(video_url):
    """Удаление видео из файловой системы по video_path"""
    static_path = STATIC_DIR
    video_file_path = os.path.normpath(os.path.join(static_path, video_url))

    try:
        if os.path.exists(video_file_path):
            os.remove(video_file_path)
            logger.info(f"--> удалено видео: '{video_url}'")
        else:
            logger.info(f"--> видео не найдено в ФС: '{video_url}'")
    except OSError as e:
        logger.error(f"--> ошибка при удалении файла '{video_url}': {e}")

def delete_color_icon_by_path(icon_url):
    """Удаление иконки цвета из файловой системы по icon_url"""
    static_path = STATIC_DIR
    icon_file_path = os.path.normpath(os.path.join(static_path, icon_url))

    try:
        if os.path.exists(icon_file_path):
            os.remove(icon_file_path)
            logger.info(f"--> удалена иконка: '{icon_url}'")
        else:
            logger.info(f"--> иконка не найдена в ФС: '{icon_url}'")
    except OSError as e:
        logger.error(f"--> ошибка при удалении файла '{icon_url}': {e}")

def save_file_to_folder(file_data, target_folder, filename):
    """
    Сохраняет file_data в target_folder с именем filename.
    Создаёт папку, если она не существует.
    """
    try:
        os.makedirs(target_folder, exist_ok=True)
        file_path = os.path.join(target_folder, filename)
        file_data.save(file_path)
        logger.info(f"--> файл '{filename}' успешно добавлен в ФС")
        return True
    except Exception as e:
        logger.error(f"--> ошибка при сохранении файла '{filename}': {e}")
        return False
    
def update_category_last_updated(category, old_categories):
    category.last_updated = datetime.now()

    help_category = category
    if help_category.parent:
        help_category = help_category.parent
        # если категория-родитель уже была, то ее обновлять не нужно
        if old_categories and help_category not in old_categories:
            help_category.last_updated = datetime.now()
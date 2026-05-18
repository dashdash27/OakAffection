from app.logger import logger
from app.extensions import STATIC_DIR, db
from app.models import Product, ProductPhoto, ProductVideo, ProductCharacteristic, Category
from app.admin.helpers import generate_unique_slug, contains_equal_photo_url, contains_equal_video_url, update_category_last_updated
from app.admin.file_cleanup import photos_to_delete, videos_to_delete
from app.helpers import get_products_by_category

import os
from datetime import datetime

def create_product_by_draft(draft):
    logger.info(f">>> Создается новый товар '{draft.name}'")

    product = Product(slug=generate_unique_slug(draft.name))
    
    db.session.add(product)
    db.session.flush()

    product = fill_product_by_draft(product, draft)
    
    return product

def fill_product_by_draft(product, draft):
    logger.debug(f"Продукт '{product.name}' заполняется данными черновика '{draft.name}'")
    product.name = draft.name
    product.price = draft.price
    product.description = draft.description
    product.application = draft.application
    product.is_new = draft.is_new
    product.ozon_link = draft.ozon_link
    product.wb_link = draft.wb_link
    product.description_tag = draft.description_tag
    product.group_id = draft.group_id
    product.color_id = draft.color_id
    product.weight = draft.weight

    product.last_updated = datetime.now()
    
    # Старый словарь с категориями
    old_products_by_categories_dict = {}
    categories = Category.query.all()
    for category in categories:
        old_products_by_categories_dict[category] = get_products_by_category(category.name)

    # Добавляем новые категории
    product.categories.clear()
    db.session.flush()
    for category in draft.categories:
        product.categories.append(category)
    db.session.flush()

    # Проверяем, что изменилось
    for category in categories:
        if old_products_by_categories_dict[category] != get_products_by_category(category.name):
            update_category_last_updated(category)
    

    product.targets.clear()
    db.session.flush()
    for target in draft.targets:
        product.targets.append(target)

    # характеристики
    product.characteristics = []
    product_chars = []
    for char in draft.characteristics:
        product_chars.append(ProductCharacteristic(
            product_id=product.id,
            characteristic_id=char.characteristic.id,
            value=char.value
        ))
    db.session.add_all(product_chars)

    # фото
    photo_urls_to_delete_set = [p.photo_url for p in product.photos]
    product.photos = []
    upload_photo_folder = os.path.join(STATIC_DIR, 'img', 'uploads')
    os.makedirs(upload_photo_folder, exist_ok=True)
    for photo in draft.photos:
        product.photos.append(ProductPhoto(
            product_id=product.id,
            photo_url=photo.photo_url,
            alt=photo.alt,
            sort_index=photo.sort_index
        ))
    for photo_url in photo_urls_to_delete_set:
        if not contains_equal_photo_url(product, photo_url):
            photos_to_delete.add(photo_url)
            logger.debug(f"-- фото '{photo_url}' было добавлено в список на удаление")
        else:
            logger.debug(f"-- фото '{photo_url}' было добавлено в список на удаление")

    # видео
    video_urls_to_delete_set = [p.video_url for p in product.videos]
    product.videos = []
    upload_video_folder = os.path.join(STATIC_DIR, 'videos', 'uploads')
    os.makedirs(upload_video_folder, exist_ok=True)
    for video in draft.videos:
        product.videos.append(ProductVideo(
            product_id=product.id,
            video_url=video.video_url,
            sort_index=video.sort_index
        ))
    for video_url in video_urls_to_delete_set:
        if not contains_equal_video_url(product, video_url):
            videos_to_delete.add(video_url)
            logger.debug(f"-- видео '{video_url}' было добавлено в список на удаление")
        else:
            logger.debug(f"-- видео '{video_url}' было добавлено в список на удаление")

    return product

def delete_draft(draft):
    logger.info(f">>> Удаляется черновик продукта '{draft.name}'")
    db.session.flush()

    # добавляем фото на удаление
    if draft.product:
        for p in draft.photos:
            if not contains_equal_photo_url(draft.product, p.photo_url):
                photos_to_delete.add(p.photo_url)
                logger.debug(f" -- фото товара '{p.photo_url}' добавлено на удаление")
            else:
                logger.debug(f" -- фото товара '{p.photo_url}' НЕ добавлено на удаление")
    else:
        for p in draft.photos:
            photos_to_delete.add(p.photo_url)
            logger.debug(f" -- фото товара'{p.photo_url}' добавлено на удаление")
        
    db.session.delete(draft)

def delete_product(product):
    # удалем продукт и вместе с ним черновик
    logger.info(f">>> Удаляется продукт '{product.name}'")
    db.session.flush()

    if product.draft:
        delete_draft(product.draft)
    
    for p in product.photos:
        photos_to_delete.add(p.photo_url)
        logger.debug(f" -- фото товара '{p.photo_url}' добавлено на удаление")

    # с категориями
    old_products_by_categories_dict = {}
    categories = Category.query.all()
    for category in categories:
        old_products_by_categories_dict[category] = get_products_by_category(category.name)

    db.session.delete(product)
    db.session.flush()

    for category in categories:
        if old_products_by_categories_dict[category] != get_products_by_category(category.name):
            update_category_last_updated(category)
    
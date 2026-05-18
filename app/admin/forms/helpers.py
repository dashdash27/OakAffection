from app.logger import logger
from app.models import Category, Target, ProductDraftCharacteristic, ProductDraftPhoto, ProductDraftVideo
from app.extensions import STATIC_DIR
from app.admin.file_cleanup import added_photos, photos_to_delete, videos_to_delete, added_videos
from app.admin.helpers import unique_img_name_gen, unique_video_name_gen, contains_equal_photo_url, contains_equal_video_url, save_file_to_folder

import os
from flask import request

def fill_draft_by_form(draft, form):
    """Заполняет объект ProductDraft данными из формы""" 
    logger.debug(">>> Черновик начал заполняться данными из формы")

    isFileSavingError = False

    # заполняем основные поля
    draft.name = form.name.data
    draft.price = form.price.data
    draft.description = form.description.data
    draft.application = form.application.data
    draft.is_new = form.is_new.data
    draft.ozon_link = form.ozon_link.data
    draft.wb_link = form.wb_link.data
    draft.description_tag = form.description_tag.data
    draft.group_id = form.group_id.data if form.group_id.data != 0 else None
    draft.color_id = form.color_id.data if form.color_id.data != 0 else None
    draft.categories = Category.query.filter(Category.id.in_(form.categories.data)).all()
    draft.targets = Target.query.filter(Target.id.in_(form.targets.data)).all()
    draft.weight = form.weight.data

    # Характеристики
    draft.characteristics = []
    for char_form in form.characteristics.entries:
        char_id = char_form.form.characteristic_id.data
        char_value = char_form.form.value.data
        if char_id and char_value:
            draft.characteristics.append(ProductDraftCharacteristic(
                product_draft_id=draft.id,
                characteristic_id=char_id,
                value=char_value
            ))

    # Работа с фото
    upload_photo_folder = os.path.join(STATIC_DIR, 'img', 'uploads')
    os.makedirs(upload_photo_folder, exist_ok=True)
    original_photos = draft.photos[:]
    original_photos_set = set(original_photos)

    logger.debug(f"Исходные фото черновика (всего {len(original_photos_set)} фото):")
    for p in original_photos_set:
        logger.debug(f"-- {p.photo_url}")

    draft.photos = []
    indices = set()
    for key in request.files:
        if key.startswith('photos-') and key.endswith('-photo'):
            num = key.split('-')[1]
            indices.add(num)

    logger.debug(f"Количество новых фото у черновика: {len(indices)}")
    logger.debug(f">>> Началось обновление фото у черновика:")
    for i in indices:
        logger.debug(f"Обработка {i} фото")
        file_data = request.files.get(f'photos-{i}-photo')
        num = request.form.get(f'photos-{i}-num')
        alt = request.form.get(f'photos-{i}-alt')

        if file_data and file_data.filename:
            filename = unique_img_name_gen(draft, file_data)
            if num:
                logger.debug(f"--> обновление фото в черновике: '{filename}'")
            else:
                logger.debug(f"--> добавление фото в черновике: '{filename}'")
                
            success = save_file_to_folder(file_data, upload_photo_folder, filename)

            if success:
                added_photos.add(f'img/uploads/{filename}')
                draft.photos.append(ProductDraftPhoto(
                    product_draft_id=draft.id,
                    photo_url=f'img/uploads/{filename}',
                    alt=alt,
                    sort_index=i
                ))
            else: 
                isFileSavingError = True
        else:
            if num:
                photo = original_photos[int(num)]
                photo.alt = request.form.get(f'photos-{i}-alt')
                photo.sort_index = i
                draft.photos.append(photo)
                logger.debug(f"--> фото не изменилось, сохраняется в черновике: '{photo.photo_url}")
                original_photos_set.remove(original_photos[int(num)])

    logger.debug(">>> Фильтр фото, которые могут удалиться:")
    for p in original_photos_set:
        if draft.product:
            if not contains_equal_photo_url(draft.product, p.photo_url):
                photos_to_delete.add(p.photo_url)
                logger.debug(f"-- фото добавлено на удаление: '{p.photo_url}'")
            else:
                logger.debug(f"-- фото НЕ добавлено на удаление: '{p.photo_url}'")
        else:
            photos_to_delete.add(p.photo_url)
            logger.debug(f"-- фото добавлено на удаление: '{p.photo_url}'")
    logger.info("<<< Добавление фото на удаление завершилось")

    logger.info("Добавлены на удаление фото:")
    for photo in photos_to_delete:
        logger.info(f"-- '{photo}'")

    # Работа с видео
    upload_video_folder = os.path.join(STATIC_DIR, 'videos', 'uploads')
    os.makedirs(upload_video_folder, exist_ok=True)
    original_videos = draft.videos[:]
    original_videos_set = set(original_videos)

    logger.debug(f"Исходные видео черновика (всего {len(original_videos_set)} фото):")
    for p in original_videos_set:
        logger.debug(f"-- {p.video_url}")

    draft.videos = []
    indices = set()
    for key in request.files:
        if key.startswith('videos-') and key.endswith('-video'):
            num = key.split('-')[1]
            indices.add(num)

    logger.debug(f"Количество новых видео у черновика: {len(indices)}")
    logger.debug(f">>> Началось обновление видер у черновика:")
    for i in indices:
        logger.debug(f"Обработка {i} видео")
        file_data = request.files.get(f'videos-{i}-video')
        num = request.form.get(f'videos-{i}-num')

        if file_data and file_data.filename:
            filename = unique_video_name_gen(draft, file_data)
            if num:
                    logger.debug(f"--> обновление видео в черновике: '{filename}'")
            else:
                logger.debug(f"--> добавление видео в черновике: '{filename}'")
                
            success = save_file_to_folder(file_data, upload_video_folder, filename)

            if success:
                added_videos.add(f'videos/uploads/{filename}')
                draft.videos.append(ProductDraftVideo(
                    product_draft_id=draft.id,
                    video_url=f'videos/uploads/{filename}',
                    sort_index=i
                ))
            else: 
                isFileSavingError = True
        else:
            if num:
                video = original_videos[int(num)]
                video.sort_index = i
                draft.videos.append(video)
                logger.debug(f"--> видео не изменилось, сохраняется в черновике: '{video.video_url}")
                original_videos_set.remove(original_videos[int(num)])

    logger.debug(">>> Фильтр видео, которые могут удалиться:")
    for p in original_videos_set:
        if draft.product:
            if not contains_equal_video_url(draft.product, p.video_url):
                videos_to_delete.add(p.video_url)
                logger.debug(f"-- видео добавлено на удаление: '{p.video_url}'")
            else:
                logger.debug(f"-- видео НЕ добавлено на удаление: '{p.video_url}'")
        else:
            videos_to_delete.add(p.video_url)
            logger.debug(f"-- video добавлено на удаление: '{p.video_url}'")
    logger.debug("<<< Добавление видео на удаление завершилось <<<")

    logger.info(f"Добавлены на удаление видео:")
    for video in videos_to_delete:
        logger.info(f"-- '{video}'")

    logger.debug("<<< Черновик заполнен данными из формы <<<")
    
    return draft, isFileSavingError

def fill_form_by_product(form, product):
    """Дозаполняет форму данными существующего продукта или черновика"""
    form.categories.data = [c.id for c in product.categories]
    form.targets.data = [t.id for t in product.targets]
    form.color_id.data = product.color_id or 0

    form.photos.entries = []
    for num, photo in enumerate(product.photos):
        form.photos.append_entry({'alt': photo.alt, 'num': num})

    form.videos.entries = []
    for num, _ in enumerate(product.videos):
        form.videos.append_entry({'num': num})
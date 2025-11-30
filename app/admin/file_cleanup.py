from app.extensions import db
from app.logger import logger
from app.admin.helpers import delete_photo_by_path, delete_video_by_path, delete_color_icon_by_path

photos_to_delete = set()
videos_to_delete = set()
icons_to_delete = set()

added_photos = set()
added_videos = set()
added_icons = set()

@db.event.listens_for(db.session, 'after_rollback')
def after_rollback(session):
    logger.warning(f"!!! Произошел rollback !!!")
    photos_to_delete.clear()
    videos_to_delete.clear()
    icons_to_delete.clear()

    # удаляем все добавленные фото из ФС
    for photo in added_photos:
        delete_photo_by_path(photo)
    for video in added_videos:
        delete_video_by_path(video)
    for icon in added_icons:
        delete_color_icon_by_path(video)
    added_photos.clear()
    added_videos.clear()
    added_icons.clear()


@db.event.listens_for(db.session, 'after_commit')
def after_commit(session):
    
    logger.info(f">>> Работа с ФС после коммита началась")

    if photos_to_delete != []:
        logger.info(f"Список фото для удаления:")
        for photo in photos_to_delete:
            logger.info(f"-- '{photo}'")
    else:
        logger.info(f"Фото для удаления нет")

    if videos_to_delete != []:
        logger.info(f"Список видео для удаления:")
        for video in videos_to_delete:
            logger.info(f"-- '{video}'")
    else:
        logger.info(f"Видео для удаления нет")

    if icons_to_delete != []:
        logger.info(f"Список иконок для удаления:")
        for icon in icons_to_delete:
            logger.info(f"-- '{icon}'")
    else:
        logger.info(f"Иконок для удаления: иконок нет")


    error_count = 0
    for photo_url in photos_to_delete:
        try:
            delete_photo_by_path(photo_url)
        except Exception as e:
            error_count += 1
    if error_count > 0:
        logger.warning(f"Удаление фотографий завершилось с {error_count} ошибками")
    else:
        logger.info(f"Удаление фотографий завершилось успешно")

    error_count = 0
    for video_url in videos_to_delete:
        try:
            delete_video_by_path(video_url)
        except Exception as e:
            error_count += 1
    if error_count > 0:
        logger.warning(f"Удаление видео завершилось с {error_count} ошибками")
    else:
        logger.info(f"Удаление видео завершилось успешно")

    error_count = 0
    for icon_url in icons_to_delete:
        try:
            delete_color_icon_by_path(icon_url)
        except Exception as e:
            error_count += 1
    if error_count > 0:
        logger.warning(f"Удаление иконок завершилось с {error_count} ошибками")
    else:
        logger.info(f"Удаление иконок завершилось успешно")


    if added_photos != []:
        logger.info(f"Список добавленных фото:")
        for photo in added_photos:
            logger.info(f"-- '{photo}'")
    else:
        logger.info(f"Добавленных фото нет")

    if added_videos != []:
        logger.info(f"Список добавленных видео:")
        for video in added_videos:
            logger.info(f"-- '{video}'")
    else:
        logger.info(f"Добавленных видео нет")

    if added_icons != []:
        logger.info(f"Список добавленных иконок:")
        for icon in added_icons:
            logger.info(f"-- '{icon}'")
    else:
        logger.info(f"Добавленных иконок нет")
    
    photos_to_delete.clear()
    added_photos.clear()

    videos_to_delete.clear()
    added_videos.clear()

    icons_to_delete.clear()
    added_icons.clear()

    logger.info("<<< Работа с файлами после коммита завершена")
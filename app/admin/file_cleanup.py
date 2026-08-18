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
    error_count = 0
    for photo_url in photos_to_delete:
        try:
            delete_photo_by_path(photo_url)
        except Exception as e:
            error_count += 1

    error_count = 0
    for video_url in videos_to_delete:
        try:
            delete_video_by_path(video_url)
        except Exception as e:
            error_count += 1

    error_count = 0
    for icon_url in icons_to_delete:
        try:
            delete_color_icon_by_path(icon_url)
        except Exception as e:
            error_count += 1

    
    photos_to_delete.clear()
    added_photos.clear()

    videos_to_delete.clear()
    added_videos.clear()

    icons_to_delete.clear()
    added_icons.clear()

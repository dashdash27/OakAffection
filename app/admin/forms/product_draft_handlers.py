from app.extensions import db
from app.admin.forms import ProductCharacteristicForm
from app.logger import logger
from app.admin.file_cleanup import photos_to_delete, videos_to_delete
from app.admin.helpers import contains_equal_photo_url, contains_equal_video_url
from app.admin.forms.helpers import fill_draft_by_form, fill_form_by_product
from app.models import (
    ProductGroup, Color, Characteristic,
    ProductDraft
)

from flask import flash, render_template, redirect, url_for


def add_product_draft(draft):
    name = draft.name
    try:
        db.session.add(draft)
        db.session.commit()
        logger.info(f"Черновик товара успешно создан: '{name}'")
        return True, None, name, draft
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при создании черновика продукта '{name}': {str(e)}")
        return False, str(e), name, draft
    
def delete_product_draft(draft_id):
    name = ''
    try:
        draft = ProductDraft.query.get(draft_id)
        if not draft:
            logger.error(f"Ошибка при удалении черновика товара: черновик не найден")
            return False, "Черновик не найден", ''
        name = draft.name

        # обрабатываем список фото, которые возможно пойдут на удаление
        for photo in draft.photos:
            if draft.product:
                if not contains_equal_photo_url(draft.product, photo.photo_url):
                    photos_to_delete.add(photo.photo_url)
                    logger.debug(f"-- фото добавлено в список на удаление: '{photo.photo_url}'")
                else:
                    logger.debug(f"-- фото не добавлено в список на удаление: '{photo.photo_url}'")
            else:
                photos_to_delete.add(photo.photo_url)
                logger.debug(f"-- фото добавлено в список на удаление: '{photo.photo_url}'")
        
        # обрабатываем список видео, которые возможно пойдут на удаление
        for video in draft.videos:
            if draft.product:
                if not contains_equal_video_url(draft.product, video.video_url):
                    videos_to_delete.add(video.video_url)
                    logger.debug(f"-- видео добавлено в список на удаление: '{video.video_url}'")
                else:
                    logger.debug(f"-- видео не добавлено в список на удаление: '{video.video_url}'")
            else:
                videos_to_delete.add(video.video_url)
                logger.debug(f"-- видео добавлено в список на удаление: '{video.video_url}'")


        db.session.delete(draft)
        db.session.commit()
        logger.info(f"Черновик товара успешно удален: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении черновика товара '{name}': {str(e)}")
        return False, str(e), name
    
def update_product_draft(draft_id, form, new_data):
    logger.info(">>> Обновление черновика продукта началось >>>")
    old_name = ''
    name = ''
    try:
        draft = ProductDraft.query.get(draft_id)
        if not draft:
            logger.error(f"Ошибка при обновлении черновика: черновик не найден")
            logger.info("<<< Обновление черновика продукта завершилось")
            return False, "Черновик не найден", ''
        
        old_name = draft.name
        draft.photos = new_data.get('photos', draft.photos)
        draft.videos = new_data.get('videos', draft.videos)
        draft, isFileSavingError = fill_draft_by_form(draft, form)
        name = draft.name

        db.session.commit()

        if not isFileSavingError:
            logger.info(f"Черновик товара успешно обновлен: '{name}'")
        else:
            logger.info(f"Черновик товара '{name}' обновлен, но некоторые файлы обновить не получилось")
        logger.info("<<< Обновление черновика продукта завершилось <<<")
        return True, None, name, draft, isFileSavingError
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении черновика '{old_name}': {str(e)}")
        logger.info("<<< Обновление черновика продукта завершилось <<<")
        return False, str(e), old_name, draft, None


def create_product_draft_handler(form, method):
    """Обработчик создания нового товара (создается черновик)"""
    page_title, button_name = "Добавление нового товара", "Создать товар"

    group_char_map = {g.id: (g.characteristic_id or '') for g in ProductGroup.query.all()}
    form.group_id.choices = [(0, 'Выберите группу')] + [(g.id, g.name) for g in ProductGroup.query.all()]
    color_group_map = {c.id: (c.category.name or '') for c in Color.query.all()}
    form.color_id.choices = [(0, 'Выберите цвет')] + [(g.id, g.name) for g in Color.query.all()]
    empty_char = ProductCharacteristicForm()
    empty_char.characteristic_id.choices = [(c.id, c.name) for c in Characteristic.query.all()]

    if method.upper() == "POST":
        if form.validate_on_submit():
            draft, isFileSavingError = fill_draft_by_form(ProductDraft(), form)

            success, error, name, draft = add_product_draft(draft)
            if success:
                if not isFileSavingError:
                    flash(f"Новый товар успешно создан: '{name}'. Данные еще не опубликованы на сайт, новый товар пока хранится в черновиках. Изменения будут опубликованы после подтверждения на главной странице админки.", "success")
                else:
                    flash(f"Новый товар создан: '{name}', но некоторые фото добавить не получилось. Данные еще не опубликованы на сайт, новый товар пока хранится в черновиках. Изменения будут опубликованы после подтверждения на главной странице админки.", "info")
                return redirect(url_for('admin.product_list'))
            else:
                flash(f"Ошибка при создании нового товара '{name}': {error}", "error")
        elif form.errors:
            flash(f"{form.errors}", 'warning')

    return render_template('admin/product_form.html',
                           form=form,
                           group_char_map=group_char_map,
                           color_group_map=color_group_map,
                           empty_char=empty_char,
                           page_title=page_title,
                           button_name=button_name)

def edit_product_draft_handler(form, method, draft_id):
    """Обработка редактирования черновика, привязанного к продукту"""
    page_title, button_name = "Редактирование товара", "Сохранить изменения"

    draft = ProductDraft.query.get_or_404(draft_id)

    form.group_id.choices = [(0, 'Выберите группу')] + [(g.id, g.name) for g in ProductGroup.query.all()]
    form.color_id.choices = [(0, 'Выберите цвет')] + [(g.id, g.name) for g in Color.query.all()]
    empty_char = ProductCharacteristicForm()
    empty_char.characteristic_id.choices = [(c.id, c.name) for c in Characteristic.query.all()]
    color_group_map = {c.id: (c.category.name or '') for c in Color.query.all()}
    group_char_map = {g.id: (g.characteristic_id or '') for g in ProductGroup.query.all()}

    photo_urls = [photo.photo_url for photo in draft.photos]
    video_urls = [video.video_url for video in draft.videos]

    if method.upper() == "GET":
        fill_form_by_product(form, draft)
    elif method.upper() == "POST":
        if form.validate_on_submit():
            logger.info(f">>> Товар '{draft.name}' редактируется (черновик есть)")

            success, error, name, draft, isFileSavingError = update_product_draft(draft.id, form, {})
            if success:
                if not isFileSavingError:
                    flash(f"Товар '{name}' успешно редактирован", 'success')
                else:
                    flash(f"Товар '{name}' редактирован, но некоторые фото добавить не получилось", 'info')
                return redirect(url_for('admin.product_list'))
            else:
                flash(f"Ошибка при редактировании товара '{name}': {error}", 'error')
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')

    return render_template('admin/product_form.html',
                           form=form,
                           group_char_map=group_char_map,
                           color_group_map=color_group_map,
                           empty_char=empty_char,
                           page_title=page_title,
                           button_name=button_name,
                           photo_urls=photo_urls,
                           video_urls=video_urls)

def edit_product_orphan_draft_handler(form, method, draft_id):
    """Обработчик редактирования товара (непривязанного к продукту)"""
    page_title, button_name = "Редактирование товара", "Сохранить изменения"

    draft = ProductDraft.query.get_or_404(draft_id)

    form.group_id.choices = [(0, 'Выберите группу')] + [(g.id, g.name) for g in ProductGroup.query.all()]
    form.color_id.choices = [(0, 'Выберите цвет')] + [(g.id, g.name) for g in Color.query.all()]
    empty_char = ProductCharacteristicForm()
    empty_char.characteristic_id.choices = [(c.id, c.name) for c in Characteristic.query.all()]
    color_group_map = {c.id: (c.category.name or '') for c in Color.query.all()}
    group_char_map = {g.id: (g.characteristic_id or '') for g in ProductGroup.query.all()}

    photo_urls = [photo.photo_url for photo in draft.photos]
    video_urls = [video.video_url for video in draft.videos]

    if method.upper() == "GET":
        fill_form_by_product(form, draft)
    elif method.upper() == "POST":
        if form.validate_on_submit():
            logger.info(f">>> Новый товар '{draft.name}' редактируется")

            success, error, name, draft, isFileSavingError = update_product_draft(draft.id, form, {})
            if success:
                if not isFileSavingError:
                    flash(f"Новый товар '{name}' успешно редактирован", 'success')
                else:
                    flash(f"Новый товар '{name}' редактирован, но некоторые фото добавить не получилось", 'info')
                return redirect(url_for('admin.product_list'))
            else:
                flash(f"Ошибка при редактировании нового товара '{name}': {error}", 'error')
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')

    return render_template('admin/product_form.html',
                           form=form,
                           group_char_map=group_char_map,
                           color_group_map=color_group_map,
                           empty_char=empty_char,
                           page_title=page_title,
                           button_name=button_name,
                           photo_urls=photo_urls,
                           video_urls=video_urls
                           )

def delete_product_draft_handler(draft_id):
    """Обработчик удаления черновика"""
    success, error, name = delete_product_draft(draft_id)
    if success:
        flash(f"Черновик товара '{name}' успешно удален ", 'success')
    else:
        flash(f"Ошибка при удалении черновика товара '{name}': {error}", "error")

    return redirect(url_for('admin.product_list'))
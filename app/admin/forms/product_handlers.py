from app.extensions import db
from app.admin.forms import ProductCharacteristicForm
from app.logger import logger
from app.admin.forms.helpers import fill_form_by_product
from app.admin.forms.product_draft_handlers import add_product_draft, update_product_draft
from app.models import (
    Product, ProductGroup, Color, Characteristic, ProductWrapper,
    ProductDraft, ProductDraftPhoto, ProductDraftVideo
)

from flask import flash, render_template, redirect, url_for, request


def edit_product_handler(form, method, product_id):
    """Редактирование товара, у которого еще нет черновика"""
    page_title, button_name = "Редактирование товара", "Сохранить изменения"
    
    product = Product.query.get_or_404(product_id)
    
    form.group_id.choices = [(0, 'Выберите группу')] + [(g.id, g.name) for g in ProductGroup.query.all()]
    form.color_id.choices = [(0, 'Выберите цвет')] + [(g.id, g.name) for g in Color.query.all()]
    form.wrapper_id.choices = [(0, 'Выберите коробку-обертку')] + [(g.id, g.name) for g in ProductWrapper.query.all()]
    empty_char = ProductCharacteristicForm()
    empty_char.characteristic_id.choices = [(c.id, c.name) for c in Characteristic.query.all()]
    color_group_map = {c.id: (c.category.name or '') for c in Color.query.all()}
    group_char_map = {g.id: (g.characteristic_id or '') for g in ProductGroup.query.all()}
    wrapper_map = {c.id: (f"{c.length} x {c.depth} x {c.height} см" or '') for c in ProductWrapper.query.all()}

    photo_urls = [photo.photo_url for photo in product.photos]
    video_urls = [video.video_url for video in product.videos]

    if method.upper() == "GET":
        fill_form_by_product(form, product)
    elif method.upper() == "POST":
        if form.validate_on_submit():
            logger.info(f">>> Товар '{product.name}' редактируется (черновика нет)")

            success, error, name, draft = add_product_draft(ProductDraft(product_id=product.id))
            if success:
                success, error, name, draft, isFileSavingError = update_product_draft(draft.id, form, {
                    'photos': [ProductDraftPhoto(product_draft_id=draft.id, photo_url=p.photo_url, alt=p.alt) for p in product.photos],
                    'videos': [ProductDraftVideo(product_draft_id=draft.id, video_url=v.video_url) for v in product.videos]
                })
                if success:
                    if not isFileSavingError:
                        flash(f"Товар '{name}' был успешно редактирован. Данные еще не опубликованы на сайте, обновленный товар пока хранится в черновиках. Изменения будут опубликованы после подтверждения на главной странице.", 'success')
                    else:
                        flash(f"Товар '{name}' был редактирован, но некоторые фото добавить не получилось. Данные еще не опубликованы на сайте, обновленный товар пока хранится в черновиках. Изменения будут опубликованы после подтверждения на главной странице.", 'info')
                    return redirect(url_for('admin.product_list'))
                else:
                    flash(f"Ошибка при редактировании товара '{name}': {error}", 'error')
            else:
                flash(f"Ошибка при редактировании товара '{product.name}': {error}", "error")
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'error')
            
            logger.info(f"<<< Редактирование товара завершилось <<< ")

    return render_template('admin/product_form.html',
                           form=form,
                           group_char_map=group_char_map,
                           color_group_map=color_group_map,
                           wrapper_map=wrapper_map,
                           empty_char=empty_char,
                           page_title=page_title,
                           button_name=button_name,
                           photo_urls=photo_urls,
                           video_urls=video_urls)


def mark_product_for_delete_handler(product_id):
    """Обработчик пометки на удаление продукта"""
    product = Product.query.get(product_id)

    if product:
        try:
            product.delete_mark = not product.delete_mark
            db.session.commit()

            if product.delete_mark:
                logger.info(f"Товар '{product.name}' был помечен на удаление")
                flash(f"Товар '{product.name}' был помечен на удаление", 'info')
            else:
                logger.info(f"Товар '{product.name}' был снят с удаления")
                flash(f"Товар '{product.name}' был снят с удаления", 'info')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при изменении статуса удаления товара '{product.name}': {str(e)}")
            flash(f"Ошибка при изменении статуса удаления у товара '{product.name}'", 'error')
    else:
        logger.error(f"Ошибка при изменении статуса удаления товара: товар не найден")
        flash("Ошибка при изменении статуса удаления товара: товар не найден", 'error')
    
    return redirect(request.referrer or '/')
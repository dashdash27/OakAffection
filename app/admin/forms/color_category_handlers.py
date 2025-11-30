from app.extensions import db
from app.models import ColorCategory
from app.logger import logger
from app.admin.helpers import delete_color_icon_by_path

from flask import render_template, flash, redirect, url_for


def add_color_category(category):
    name = category.name
    try:
        db.session.add(category)
        db.session.commit()
        logger.info(f"Категория цветов успешно создана: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при добавлении категории цвета: '{name}': {str(e)}")
        return False, str(e), name
    
def update_color_category(category_id, new_data):
    old_name = ''
    name = ''
    try:
        category = ColorCategory.query.get(category_id)
        if not category:
            logger.error(f"Ошибка при обновлении категории цвета: категория цвета не найдена")
            return False, "Категория цвета не найдена", ''
        
        old_name = category.name
        category.name = new_data.get('name', category.name)
        name = category.name

        db.session.commit()

        logger.info(f"Категория цвета успешно обновлена: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении категории цвета '{old_name}': {str(e)}")
        return False, str(e), old_name
    
def delete_color_category(category_id):
    name = ''
    try:
        category = ColorCategory.query.get(category_id)
        if not category:
            logger.error(f"Ошибка при удалении категории цвета: категория цвета не найдена")
            return False, "Категория цвета не найдена", ''
        
        # удаляем все иконки цветов из категории
        for color in category.colors:
            if color.icon_url:
                delete_color_icon_by_path(color.icon_url)
        
        name = category.name
        db.session.delete(category)
        db.session.commit()
        logger.info(f"Категория цвета успешно удалена: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении категории цвета '{name}': {str(e)}")
        return False, str(e), name
    
def create_color_category_handler(form, method):
    page_title = "Добавление новой категории цвета"
    button_name = "Создать"

    if method == "POST":
        if form.validate_on_submit():
            category = ColorCategory(
                name=form.name.data
            )
            success, error, name = add_color_category(category)
            if success:
                flash(f"Новая категория цвета успешно создана: '{name}'", "success")
                return redirect(url_for('admin.color_category_list'))
            else:
                flash(f"Ошибка при создании категории цвета '{name}': {error}", "error")
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')
    
    return render_template('admin/color_category_form.html', 
                form=form,
                page_title=page_title,
                button_name=button_name)

def edit_color_category_handler(form, method, category_id):
    page_title = "Редактирование категории цвета"
    button_name = "Сохранить изменения"

    category = ColorCategory.query.get_or_404(category_id)

    if method.upper() == "POST":
        if form.validate_on_submit():
            success, error, name = update_color_category(category_id, {
                'name': ' '.join(form.name.data.split())
            })
            if success:
                flash(f"Категория цвета успешно обновлена: '{name}'", 'success')
                return redirect(url_for('admin.color_category_list'))
            else:
                flash(f"Ошибка при обновлении категории цвета '{name}': {error}", 'error')
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')
    
    return render_template('admin/color_category_form.html', 
                    form=form,
                    page_title=page_title,
                    button_name=button_name,
                    category=category)

def delete_color_category_handler(category_id):
    success, error, name = delete_color_category(category_id)
    if success:
        flash(f"Категория цвета успешно удалена: '{name}' ", 'success')
    else:
        flash(f"Ошибка при удалении категории цвета '{name}': {error}", "error")

    return redirect(url_for('admin.color_category_list'))

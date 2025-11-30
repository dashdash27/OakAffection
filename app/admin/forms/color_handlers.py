from app.extensions import db, STATIC_DIR
from app.models import Color
from app.logger import logger
from app.admin.helpers import unique_color_icon_name_gen, save_file_to_folder, delete_color_icon_by_path
from app.admin.file_cleanup import icons_to_delete, added_icons

from flask import render_template, flash, redirect, url_for
import os


def add_color(color):
    name = color.name
    try:
        db.session.add(color)
        db.session.commit()
        logger.info(f"Цвет успешно создан: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при добавлении цвета '{name}': {str(e)}")
        return False, str(e), name
    
def update_color(color_id, new_data):
    old_name = ''
    name = ''
    try:
        color = Color.query.get(color_id)
        if not color:
            logger.error(f"Ошибка при обновлении цвета: цвет не найден")
            return False, "Цвет не найден", ''
        
        old_name = color.name
        color.name = new_data.get('name', color.name)
        color.category_id = new_data.get('category_id', color.category_id)
        color.icon_url = new_data.get('icon_url', color.icon_url)
        name = color.name

        db.session.commit()

        logger.info(f"Цвет успешно обновлен: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении цвета '{old_name}': {str(e)}")
        return False, str(e), old_name
    
def delete_color(color_id):
    name = ''
    try:
        color = Color.query.get(color_id)
        if not color:
            logger.error(f"Ошибка при удалении цвета: цвет не найден")
            return False, "Цвет не найден", ''
        
        name = color.name
        if color.icon_url:
            delete_color_icon_by_path(color.icon_url)

        db.session.delete(color)
        db.session.commit()
        logger.info(f"Цвет успешно удален: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении цвета '{name}': {str(e)}")
        return False, str(e), name
    
def change_color_icon(file_data, old_icon_url):
    isFileSavingError = False
    icon_url = old_icon_url

    upload_icon_folder = os.path.join(STATIC_DIR, 'img', 'colors')


    if file_data and getattr(file_data, 'filename', None):
        logger.debug("У цвета новая иконка")
        filename = unique_color_icon_name_gen(file_data)
        success = save_file_to_folder(file_data, upload_icon_folder, filename)

        if success:
            if old_icon_url:
                icons_to_delete.add(old_icon_url)
            added_icons.add(f'img/colors/{filename}')
            icon_url = f'img/colors/{filename}'
            logger.info(f"Новая иконка успешно сохранена в ФС: '{icon_url}'")
        else:
            isFileSavingError = True
            logger.info(f"Произошла ошибка при сохранении иконки цвета в ФС: '{icon_url}'")

    return icon_url, isFileSavingError
    
def create_color_handler(form, method):
    page_title = "Добавление нового цвета"
    button_name = "Создать"

    if method == "POST":
        if form.validate_on_submit():
            # добавляем фото если есть
            icon_url, isFileSavingError = change_color_icon(form.icon.data, None)

            color = Color(
                name=form.name.data,
                category_id=form.category_id.data if form.category_id.data != 0 else None,
                icon_url=icon_url
            )
            success, error, name = add_color(color)
            if success:
                if not isFileSavingError:
                    flash(f"Новый цвет успешно создан: '{name}'", "success")
                else:
                    flash(f"Новый цвет создан: '{name}'. Но иконку загрузить не получилось, произошла ошибка.", "warning")
                return redirect(url_for('admin.color_list'))
            else:
                flash(f"Ошибка при создании цвета '{name}': {error}", "error")
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')
    
    return render_template('admin/color_form.html', 
                    form=form,
                    page_title=page_title,
                    button_name=button_name)

def edit_color_handler(form, method, color_id):
    page_title = "Редактирование цвета"
    button_name = "Сохранить изменения"

    color = Color.query.get_or_404(color_id)

    if method.upper() == "GET":
        form.category_id.data = color.category_id or 0
    elif method.upper() == "POST":
        if form.validate_on_submit():
            # меняем иконку цвета
            icon_url, isFileSavingError = change_color_icon(form.icon.data, color.icon_url)

            success, error, name = update_color(color_id, {
                'name': ' '.join(form.name.data.split()),
                'category_id': form.category_id.data,
                'icon_url': icon_url
            })
            if success:
                if not isFileSavingError:
                    flash(f"Цвет успешно обновлен: '{name}'", 'success')
                else:
                    flash(f"Цвет обновлен: '{name}'. Но иконку обновить не получилось, произошла ошибка.", 'warning')
                return redirect(url_for('admin.color_list'))
            else:
                flash(f"Ошибка при обновлении цвета '{name}': {error}", 'error')
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')
    
    return render_template('admin/color_form.html', 
                    form=form,
                    page_title=page_title,
                    button_name=button_name, color=color)

def delete_color_handler(color_id):
    success, error, name = delete_color(color_id)
    if success:
        flash(f"Цвет успешно удален: '{name}' ", 'success')
    else:
        flash(f"Ошибка при удалении цвета '{name}': {error}", "error")

    return redirect(url_for('admin.color_list'))

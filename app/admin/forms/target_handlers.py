from app.models import Target
from app.extensions import db
from app.logger import logger

from flask import render_template, flash, url_for, redirect

def add_target(target):
    name = target.name
    try:
        db.session.add(target)
        db.session.commit()
        logger.info(f"Предмет обработки успешно создан: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при добавлении предмета обработки '{name}': {str(e)}")
        return False, str(e), name
    
def update_target(target_id, new_data):
    old_name = ''
    name = ''
    try:
        target = Target.query.get(target_id)
        if not target:
            logger.error(f"Ошибка при обновлении предмета обработки: предмет обработки не найден")
            return False, "Предмет обработки не найден", ''
        old_name = target.name
        target.name = new_data.get('name', target.name)
        name = target.name

        db.session.commit()

        logger.info(f"Предмет обработки успешно обновлен: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении предмета обработки '{old_name}': {str(e)}")
        return False, str(e), old_name
    
def delete_target(target_id):
    name = ''
    try:
        target = Target.query.get(target_id)
        if not target:
            logger.error(f"Ошибка при удалении предмета обработки: предмет обработки не найден")
            return False, "Предмет обработки не найден", ''
        
        name = target.name

        db.session.delete(target)
        db.session.commit()
        logger.info(f"Предмет обработки успешно удален: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении предмета обработки '{name}': {str(e)}")
        return False, str(e), name

def create_target_handler(form, method):
    page_title = "Добавление предмета обработки"
    button_name = "Создать"

    if method.upper() == "POST":
        if form.validate_on_submit():
            target = Target(name = ' '.join(form.name.data.split()))
            success, error, name = add_target(target)
            if success:
                flash(f"Новый предмет обработки успешно создан: '{name}'", "success")
                return redirect(url_for('admin.target_list'))
            else:
                flash(f"Ошибка при создании предмета обработки '{name}': {error}", "error")
    else:
        if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')

    return render_template('admin/target_form.html',
                        form=form,
                        page_title=page_title,
                        button_name=button_name)

def edit_target_handler(form, method, target_id):
    page_title = "Редактирование предмета обработки"
    button_name = "Сохранить изменения"

    target = Target.query.get(target_id)

    if method == "POST":
        if form.validate_on_submit():
            success, error, name = update_target(target_id, {
                'name': ' '.join(form.name.data.split())
            })
            if success:
                flash(f"Предмет обработки успешно обновлен: '{name}'", 'success')
                return redirect(url_for('admin.target_list'))
            else:
                flash(f"Ошибка при обновлении предмета обработки '{name}': {error}", 'error')
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')

    return render_template('admin/target_form.html',
                        form=form,
                        page_title=page_title,
                        button_name=button_name,
                        target=target)

def delete_target_handler(target_id):
    success, error, name = delete_target(target_id)
    if success:
        flash(f"Предмет обработки успешно удален: '{name}' ", 'success')
    else:
        flash(f"Ошибка при удалении предмета обработки '{name}': {error}", "error")

    return redirect(url_for('admin.target_list'))
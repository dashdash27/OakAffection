from app.models import Characteristic
from app.extensions import db
from app.logger import logger

from flask import flash, render_template, redirect, url_for


def add_characteristic(characteristic):
    name = characteristic.name
    try:
        db.session.add(characteristic)
        db.session.commit()
        logger.info(f"Характеристика успешно создана: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при добавлении характеристики '{name}': {str(e)}")
        return False, str(e), name
    
def update_characteristic(characteristic_id, new_data):
    old_name = ''
    name = ''
    try:
        characteristic = Characteristic.query.get(characteristic_id)
        if not characteristic:
            logger.error(f"Ошибка при обновлении характеристики: характеристика не найдена")
            return False, "Характеристика не найдена", ''

        old_name = characteristic.name
        characteristic.name = new_data.get('name', characteristic.name)
        name = characteristic.name

        db.session.commit()

        logger.info(f"Характеристика успешно обновлена: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении характеристики '{old_name}': {str(e)}")
        return False, str(e), old_name

def delete_characteristic(characteristic_id):
    name = ''
    try:
        characteristic = Characteristic.query.get(characteristic_id)
        if not characteristic:
            logger.error(f"Ошибка при удалении характеристики: характеристика не найдена")
            return False, "Характеристика не найдена", ''
        
        name = characteristic.name

        db.session.delete(characteristic)
        db.session.commit()
        logger.info(f"Характеристика успешно удалена: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении характеристики '{name}': {str(e)}")
        return False, str(e), name

def create_characteristic_handler(form, method):
    page_title = "Добавление новой характеристики"
    button_name = "Создать характеристику"

    if method.upper() == "POST":
        if form.validate_on_submit():
            characteristic = Characteristic(name=' '.join(form.name.data.split()))
            success, error, name = add_characteristic(characteristic)
            if success:
                flash(f"Новая характеристика успешно создана: '{name}'", "success")
                return redirect(url_for('admin.characteristic_list'))
            else:
                flash(f"Ошибка при создании характеристики '{name}': {error}", "error")
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')

    return render_template('admin/characteristic_form.html', 
                    form=form,
                    page_title=page_title,
                    button_name=button_name)
        
def edit_characteristic_handler(form, method, characteristic_id):
    page_title = "Редактирование характеристики"
    button_name = "Сохранить изменения"

    if method.upper() == "POST":
        if form.validate_on_submit():
            success, error, name = update_characteristic(characteristic_id, {
                'name': ' '.join(form.name.data.split())
            })
            if success:
                flash(f"Характеристика успешно обновлена: '{name}'", 'success')
                return redirect(url_for('admin.characteristic_list'))
            else:
                flash(f"Ошибка при обновлении характеристики '{name}': {error}", 'error')
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')

    return render_template('admin/characteristic_form.html', 
                    form=form,
                    page_title=page_title,
                    button_name=button_name
                    )

def delete_characteristic_handler(characteristic_id):
    success, error, name = delete_characteristic(characteristic_id)
    if success:
        flash(f"Характеристика товаров успешно удалена: '{name}' ", 'success')
    else:
        flash(f"Ошибка при удалении характеристики '{name}': {error}", "error")

    return redirect(url_for('admin.characteristic_list'))
from app.models import ProductGroup
from app.extensions import db
from app.logger import logger

from flask import render_template, flash, redirect, url_for


def add_product_group(group):
    name = group.name
    try:
        db.session.add(group)
        db.session.commit()
        logger.info(f"Группа товаров успешно создана: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при добавлении группы товаров '{name}': {str(e)}")
        return False, str(e), name
    
def update_product_group(group_id, new_data):
    old_name = ''
    name = ''
    try:
        group = ProductGroup.query.get(group_id)
        if not group:
            logger.error(f"Ошибка при обновлении группы товаров: группа товаров не найдена")
            return False, "Группа товаров не найдена", ''
        
        old_name = group.name
        group.name = new_data.get('name', group.name)
        group.characteristic_id = new_data.get('characteristic_id', group.characteristic_id)
        name = group.name

        db.session.commit()

        logger.info(f"Группа товаров успешно обновлена: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении группы товаров '{old_name}': {str(e)}")
        return False, str(e), old_name

def delete_product_group(group_id):
    name = ''
    try:
        group = ProductGroup.query.get(group_id)
        if not group:
            logger.error(f"Ошибка при удалении группы товаров: группа товаров не найдена")
            return False, "Группа товаров не найдена", ''
        
        name = group.name
        db.session.delete(group)
        db.session.commit()
        logger.info(f"Группа товаров успешно удалена: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении группы товаров '{name}': {str(e)}")
        return False, str(e), name

def create_product_group_handler(form, method):
    page_title = "Добавление новой группы товаров"
    button_name = "Создать"

    if method == "POST":
        if form.validate_on_submit():
            group = ProductGroup(
                name=form.name.data,
                characteristic_id=form.characteristic_id.data
            )
            success, error, name = add_product_group(group)
            if success:
                flash(f"Новая группа товаров успешно создана: '{name}'", "success")
                return redirect(url_for('admin.product_group_list'))
            else:
                flash(f"Ошибка при создании группы товаров '{name}': {error}", "error")
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')

    return render_template('admin/product_group_form.html', 
                    form=form,
                    page_title=page_title,
                    button_name=button_name)

def edit_product_group_handler(form, method, group_id):
    page_title = "Редактирование группы товаров"
    button_name = "Сохранить изменения"

    group = ProductGroup.query.get_or_404(group_id)

    if method.upper() == "GET":
        form.characteristic_id.data = group.characteristic_id
    elif method.upper() == "POST":
        if form.validate_on_submit():
            # проверка, отправилась ли характеристика
            new_data = {'name': ' '.join(form.name.data.split())}
            if form.characteristic_id.data:
                new_data['characteristic_id'] = form.characteristic_id.data
            
            success, error, name = update_product_group(group_id, new_data)
            if success:
                flash(f"Группа товаров успешно обновлена: '{name}'", 'success')
                return redirect(url_for('admin.product_group_list'))
            else:
                flash(f"Ошибка при обновлении группы товаров '{name}': {error}", 'error')
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')


    return render_template('admin/product_group_form.html', 
                    form=form,
                    page_title=page_title,
                    button_name=button_name,
                    group=group)

def delete_product_group_handler(group_id):
    success, error, name = delete_product_group(group_id)
    if success:
        flash(f"Группа товаров успешно удалена: '{name}' ", 'success')
    else:
        flash(f"Ошибка при удалении группы товаров '{name}': {error}", "error")

    return redirect(url_for('admin.product_group_list'))

    
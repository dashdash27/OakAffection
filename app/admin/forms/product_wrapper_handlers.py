from app.models import ProductWrapper
from app.extensions import db
from app.logger import logger

from flask import render_template, flash, redirect, url_for


def add_product_wrapper(wrapper):
    name = wrapper.name
    try:
        db.session.add(wrapper)
        db.session.commit()
        logger.info(f"Коробка-обертка успешно создана: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при добавлении коробки-обертки '{name}': {str(e)}")
        return False, str(e), name
    
def update_product_wrapper(wrapper_id, new_data):
    old_name = ''
    name = ''
    try:
        wrapper = ProductWrapper.query.get(wrapper_id)
        if not wrapper:
            logger.error(f"Ошибка при обновлении коробки-обертки: коробка-обертка не найдена")
            return False, "Коробка-обертка не найдена", ''
        
        old_name = wrapper.name
        wrapper.name = new_data.get('name', wrapper.name)
        wrapper.length = new_data.get('length', wrapper.length)
        wrapper.depth = new_data.get('depth', wrapper.depth)
        wrapper.height = new_data.get('height', wrapper.height)
        name = wrapper.name

        db.session.commit()

        logger.info(f"Коробка-обертка успешно обновлена: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении коробки-обертки '{old_name}': {str(e)}")
        return False, str(e), old_name
    
def create_product_wrapper_handler(form, method):
    page_title = "Добавление новой группы товаров"
    button_name = "Создать"

    if method == "POST":
        if form.validate_on_submit():
            wrapper = ProductWrapper(
                name=form.name.data,
                length=form.length.data,
                depth=form.depth.data,
                height=form.height.data
            )
            success, error, name = add_product_wrapper(wrapper)
            if success:
                flash(f"Новая коробка-обертка успешно создана: '{name}'", "success")
                return redirect(url_for('admin.product_wrapper_list'))
            else:
                flash(f"Ошибка при создании коробки-обертки '{name}': {error}", "error")
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')

    return render_template('admin/product_wrapper_form.html', 
                    form=form,
                    page_title=page_title,
                    button_name=button_name)

def edit_product_wrapper_handler(form, method, wrapper_id):
    page_title = "Редактирование коробки-обертки"
    button_name = "Сохранить изменения"

    wrapper = ProductWrapper.query.get_or_404(wrapper_id)

    if method.upper() == "POST":
        if form.validate_on_submit():
            new_data = {'name': ' '.join(form.name.data.split())}
            new_data['length'] = form.length.data
            new_data['depth'] = form.depth.data
            new_data['height'] = form.height.data
            success, error, name = update_product_wrapper(wrapper_id, new_data)
            if success:
                flash(f"Коробка-обертка товаров успешно обновлена: '{name}'", 'success')
                return redirect(url_for('admin.product_wrapper_list'))
            else:
                flash(f"Ошибка при обновлении коробки-обертки товаров '{name}': {error}", 'error')
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')

    return render_template('admin/product_wrapper_form.html', 
                    form=form,
                    page_title=page_title,
                    button_name=button_name,
                    wrapper=wrapper)
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
    
def create_product_wrapper_handler(form, method):
    page_title = "Добавление новой группы товаров"
    button_name = "Создать"

    if method == "POST":
        if form.validate_on_submit():
            wrapper = ProductWrapper(
                name=form.name.data,
                length=form.length.data,
                height=form.height.data,
                width=form.width.data
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
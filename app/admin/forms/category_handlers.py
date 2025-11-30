from app.models import Category
from app.extensions import db
from app.logger import logger

from flask import render_template, flash, url_for, redirect


def add_category(category):
    name = category.name
    try:
        db.session.add(category)
        db.session.commit()
        logger.info(f"Категория успешно создана: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при добавлении категории '{name}': {str(e)}")
        return False, str(e), name
    
def update_category(category_id, new_data):
    old_name = ''
    name = ''
    try:
        category = Category.query.get(category_id)
        if not category:
            logger.error(f"Ошибка при обновлении категории: категория не найдена")
            return False, "Категория не найдена", ''
        
        old_name = category.name
        category.name = new_data.get('name', category.name)
        category.parent_id = new_data.get('parent_id')
        category.description_tag = new_data.get('description_tag')
        category.children = new_data.get('children')
        name = category.name

        db.session.commit()

        logger.info(f"Категория успешно обновлена: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении категории '{old_name}': {str(e)}")
        return False, str(e), old_name
    
def delete_category(category_id):
    name = ''
    try:
        category = Category.query.get(category_id)
        if not category:
            logger.error(f"Ошибка при удалении категории: категория не найдена")
            return False, "Категория не найдена", ''
        
        name = category.name
        db.session.delete(category)
        db.session.commit()
        logger.info(f"Категория успешно удалена: '{name}'")
        return True, None, name
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении категории '{name}': {str(e)}")
        return False, str(e), name

def create_category_handler(form, method):
    page_title = "Добавление новой категории"
    button_name = "Создать категорию"

    if method.upper() == "POST":
        if form.validate_on_submit():
            selected_children_ids = form.children.data

            category = Category(
                name=' '.join(form.name.data.split()),
                description_tag=' '.join(form.description_tag.data.split()),
                parent_id=form.parent_id.data if form.parent_id.data != 0 else None,
                children=Category.query.filter(Category.id.in_(selected_children_ids)).all()
            )
            
            success, error, name = add_category(category)
            if success:
                flash(f"Новая категория успешно создана: '{name}'", "success")
                return redirect(url_for('admin.category_list'))
            else:
                flash(f"Ошибка при создании категории '{name}': {error}", "error")
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')

    return render_template('admin/category_form.html',
                        form=form,
                        page_title=page_title,
                        button_name=button_name)

def edit_category_handler(form, method, category_id):
    page_title = "Редактирование категории"
    button_name = "Сохранить изменения"

    category = Category.query.get_or_404(category_id)

    if method.upper() == "GET":
        # удаляем из родителей себя
        form.parent_id.choices = [item for item in form.parent_id.choices if item[0] != category_id]
        # удаляем из потомков себя
        form.children.choices = [item for item in form.children.choices if item[0] != category_id]
        
        # устанавливаем родителя, потомков
        form.parent_id.data = category.parent_id or 0
        form.children.data = [c.id for c in category.children]

    elif method.upper() == "POST":
        if form.validate_on_submit():
            success, error, name = update_category(category_id, {
                'name': ' '.join(form.name.data.split()),
                'parent_id': form.parent_id.data if form.parent_id.data != 0 else None,
                'description_tag': ' '.join(form.description_tag.data.split()),
                'children': Category.query.filter(Category.id.in_(form.children.data)).all()
            })
            if success:
                flash(f"Категория успешно обновлена: '{name}'", 'success')
                return redirect(url_for('admin.category_list'))
            else:
                flash(f"Ошибка при обновлении категории '{name}': {error}", 'error')
        else:
            if form.errors:
                error_messages = '; '.join(
                    [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                )
                flash(f"Ошибки в форме: {error_messages}", 'warning')

    return render_template('admin/category_form.html',
                        form=form,
                        page_title=page_title,
                        button_name=button_name,
                        category=category)

def delete_category_handler(category_id):
    success, error, name = delete_category(category_id)
    if success:
        flash(f"Категория товаров успешно удалена: '{name}' ", 'success')
    else:
        flash(f"Ошибка при удалении категории '{name}': {error}", "error")

    return redirect(url_for('admin.category_list'))
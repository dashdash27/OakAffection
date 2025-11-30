from app.models import Product, Characteristic, Category, ProductGroup, Target, Color, ProductDraft, ColorCategory, AdminUser
from app.admin.publish import publish_all_changes
from app.extensions import limiter
from app.admin.forms import ProductForm, CategoryForm, CharacteristicForm, TargetForm, ProductGroupForm, ColorForm, ColorCategoryForm
from app.admin.forms import (
    create_characteristic_handler, 
    edit_characteristic_handler,
    create_product_draft_handler,
    edit_product_handler,
    create_category_handler,
    edit_category_handler,
    create_target_handler, 
    edit_target_handler,
    create_product_group_handler, 
    edit_product_group_handler,
    mark_product_for_delete_handler, 
    delete_target_handler,
    delete_category_handler,
    delete_characteristic_handler,
    delete_product_group_handler,
    delete_product_draft_handler, 
    edit_product_orphan_draft_handler, 
    create_color_handler,
    edit_color_handler,
    delete_color_handler, 
    create_color_category_handler,
    edit_color_category_handler,
    delete_color_category_handler,
    edit_product_draft_handler
)

from flask import Blueprint, flash, request, render_template, url_for, redirect
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.datastructures import CombinedMultiDict


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
login_bp = Blueprint('adminlogin', __name__, url_prefix='/adminlogin')

@admin_bp.before_request
def protect_admin():
    if not current_user.is_authenticated:
        return redirect(url_for('adminlogin.login'))
    
@login_bp.route('/', methods=['GET', 'POST'])
@limiter.limit("4 per minute", methods=['POST']) 
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = AdminUser.query.filter_by(username=username).first()

        if user and user.check_password(password):
            logout_user()
            login_user(user, remember=False)
            return redirect(url_for('admin.index'))
        else:
            flash('Неверный логин или пароль', "error")
    
    
    return render_template('admin/login.html')

@login_required
@login_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('adminlogin.login'))

# Index
@admin_bp.route('/')
def index():
    # получаем все объекты
    products = Product.query.all()
    categories = Category.query.all()
    targets = Target.query.all()
    characteristics = Characteristic.query.all()
    colors = Color.query.all()
    product_groups = ProductGroup.query.all()

    # получаем отдельно продукты разного типа
    updated_products = []
    delete_marked_products = []
    orphan_drafts = ProductDraft.query.filter(ProductDraft.product_id.is_(None)).all()
    
    for product in products:
        if product.draft and not product.delete_mark:
            updated_products.append(product)
        if product.delete_mark:
            delete_marked_products.append(product)
            
    return render_template('admin/home.html', 
                        updated_products=updated_products,
                        delete_marked_products=delete_marked_products,
                        orphan_drafts=orphan_drafts,
                        products=products,
                        categories=categories,
                        targets=targets,
                        characteristics=characteristics,
                        colors=colors,
                        product_groups=product_groups
                        )

# Product
@admin_bp.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'GET':
        form = ProductForm(obj=product)
    else:
        form = ProductForm(formdata=CombinedMultiDict((request.files, request.form)))
    return edit_product_handler(form, request.method, product_id)

@admin_bp.route('/mark_product_for_delete', methods=['POST'])
def mark_product_for_delete():
    product_id = request.form.get('product_id')
    return mark_product_for_delete_handler(product_id)

# Product Lists
@admin_bp.route('/product_list', methods=['GET'])
def product_list():
    products = Product.query.all()
    orphan_drafts = ProductDraft.query.filter(ProductDraft.product_id.is_(None)).all()
    return render_template('admin/lists/product_list.html', 
                            products=products,
                            orphan_drafts=orphan_drafts)

@admin_bp.route('/added_product_list', methods=['GET'])
def added_product_list():
    products = Product.query.all()
    orphan_drafts = ProductDraft.query.filter(ProductDraft.product_id.is_(None)).all()
    return render_template('admin/lists/added_product_list.html', 
                            orphan_drafts=orphan_drafts)

@admin_bp.route('/edited_product_list', methods=['GET'])
def edited_product_list():
    products = Product.query.all()
    drafts = []

    for product in products:
        if product.draft and not product.delete_mark:
            drafts.append(product.draft)

    return render_template('admin/lists/edited_product_list.html', 
                            drafts=drafts)

@admin_bp.route('/delete_marked_product_list', methods=['GET'])
def delete_marked_product_list():
    products = Product.query.all()
    delete_marked_products = []

    for product in products:
        if product.delete_mark:
            delete_marked_products.append(product)

    return render_template('admin/lists/delete_marked_product_list.html', 
                            delete_marked_products=delete_marked_products)

# Product Draft
@admin_bp.route('/edit_product_draft/<int:draft_id>', methods=['GET', 'POST'])
def edit_product_draft(draft_id):
    draft = ProductDraft.query.get_or_404(draft_id)
    if request.method == 'GET':
        form = ProductForm(obj=draft)
    else:
        form = ProductForm(formdata=CombinedMultiDict((request.files, request.form)))
    return edit_product_draft_handler(form, request.method, draft_id)
    
@admin_bp.route('/create_product_draft', methods=['GET', 'POST'])
def create_product_draft():
    form = ProductForm(CombinedMultiDict((request.files, request.form)))
    return create_product_draft_handler(form, request.method)

@admin_bp.route('/edit_product_orphan_draft/<int:draft_id>', methods=['GET', 'POST'])
def edit_product_orphan_draft(draft_id):
    draft = ProductDraft.query.get_or_404(draft_id)
    if request.method == 'GET':
        form = ProductForm(obj=draft)
    else:
        form = ProductForm(formdata=CombinedMultiDict((request.files, request.form)))
    return edit_product_orphan_draft_handler(form, request.method, draft_id)

@admin_bp.route('/delete_product_draft', methods=['POST'])
def delete_product_draft():
    draft_id = request.form.get('draft_id')
    return delete_product_draft_handler(draft_id)
    
# Characteristic
@admin_bp.route('/create_characteristic', methods=['GET', 'POST'])
def create_characteristic():
    form = CharacteristicForm()
    return create_characteristic_handler(form, request.method)
    
@admin_bp.route('/edit_characteristic/<int:characteristic_id>', methods=['GET', 'POST'])
def edit_characteristic(characteristic_id):
    characteristic = Characteristic.query.get_or_404(characteristic_id)
    if request.method == 'GET':
        form = CharacteristicForm(obj=characteristic)
    else:
        form = CharacteristicForm()
    return edit_characteristic_handler(form, request.method, characteristic_id)

@admin_bp.route('/delete_characteristic', methods=['POST'])
def delete_characteristic():
    characteristic_id = request.form.get('characteristic_id')
    return delete_characteristic_handler(characteristic_id)

@admin_bp.route('/characteristic_list', methods=['GET'])
def characteristic_list():
    chars = Characteristic.query.all()
    return render_template('admin/lists/characteristic_list.html', chars=chars)

# Category
@admin_bp.route('/create_category', methods=['GET', 'POST'])
def create_category():
    form = CategoryForm()
    return create_category_handler(form, request.method)

@admin_bp.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == 'GET':
        form = CategoryForm(obj=category)
    else:
        form = CategoryForm()
    return edit_category_handler(form, request.method, category_id)

@admin_bp.route('/delete_category', methods=['POST'])
def delete_category():
    category_id = request.form.get('category_id')
    return delete_category_handler(category_id)

@admin_bp.route('/category_list', methods=['GET'])
def category_list():
    categories = Category.query.all()
    return render_template('admin/lists/category_list.html', categories=categories)

# Target
@admin_bp.route('/create_target', methods=['GET', 'POST'])
def create_target():
    form = TargetForm()
    return create_target_handler(form, request.method)

@admin_bp.route('/edit_target/<int:target_id>', methods=['GET', 'POST'])
def edit_target(target_id):
    target = Target.query.get_or_404(target_id)
    if request.method == 'GET':
        form = TargetForm(obj=target)
    else:
        form = TargetForm()
    return edit_target_handler(form, request.method, target_id)

@admin_bp.route('/delete_target', methods=['POST'])
def delete_target():
    target_id = request.form.get('target_id')
    return delete_target_handler(target_id)

@admin_bp.route('/target_list', methods=['GET'])
def target_list():
    targets = Target.query.all()
    return render_template('admin/lists/target_list.html', targets=targets)

# Product Group
@admin_bp.route('/create_product_group', methods=['GET', 'POST'])
def create_product_group():
    form = ProductGroupForm()
    return create_product_group_handler(form, request.method)

@admin_bp.route('/edit_product_group/<int:group_id>', methods=['GET', 'POST'])
def edit_product_group(group_id):
    group = ProductGroup.query.get_or_404(group_id)
    if request.method == 'GET':
        form = ProductGroupForm(obj=group)
    else:
        form = ProductGroupForm()
    return edit_product_group_handler(form, request.method, group_id)

@admin_bp.route('/delete_product_group', methods=['POST'])
def delete_product_group():
    group_id = request.form.get('group_id')
    return delete_product_group_handler(group_id)

@admin_bp.route('/product_group_list', methods=['GET'])
def product_group_list():
    groups = ProductGroup.query.all()
    return render_template('admin/lists/product_group_list.html', groups=groups)

# Colors
@admin_bp.route('/color_list', methods=['GET'])
def color_list():
    colors = Color.query.all()
    return render_template('admin/lists/color_list.html', colors=colors)

@admin_bp.route('/create_color', methods=['GET', 'POST'])
def create_color():
    form = ColorForm()
    return create_color_handler(form, request.method)

@admin_bp.route('/edit_color/<int:color_id>', methods=['GET', 'POST'])
def edit_color(color_id):
    color = Color.query.get_or_404(color_id)
    if request.method == 'GET':
        form = ColorForm(obj=color)
    else:
        form = ColorForm()
    return edit_color_handler(form, request.method, color_id)

@admin_bp.route('/delete_color', methods=['POST'])
def delete_color():
    color_id = request.form.get('color_id')
    return delete_color_handler(color_id)

# Colors Categories
@admin_bp.route('/create_color_category', methods=['GET', 'POST'])
def create_color_category():
    form = ColorCategoryForm()
    return create_color_category_handler(form, request.method)

@admin_bp.route('/edit_color_category/<int:category_id>', methods=['GET', 'POST'])
def edit_color_category(category_id):
    category = ColorCategory.query.get_or_404(category_id)
    if request.method == 'GET':
        form = ColorCategoryForm(obj=category)
    else:
        form = ColorCategoryForm()
    return edit_color_category_handler(form, request.method, category_id)

@admin_bp.route('/delete_color_category', methods=['POST'])
def delete_color_category():
    category_id = request.form.get('color_category_id')
    return delete_color_category_handler(category_id)

@admin_bp.route('/color_category_list', methods=['GET'])
def color_category_list():
    categories = ColorCategory.query.all()
    return render_template('admin/lists/color_category_list.html', categories=categories)

# Publish changes
@admin_bp.route('/publish_changes', methods=['POST'])
def publish_changes():
    success = publish_all_changes()
    if success:
        flash("Изменения подтверждены")
    else:
        flash("Не удалось подтвердить изменения")
    
    return redirect(url_for("admin.index"))
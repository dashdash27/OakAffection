from app.models import Category, Characteristic, Target, ProductGroup, ColorCategory

from flask_wtf import FlaskForm, Form
from flask_wtf.file import FileField
from wtforms.validators import DataRequired, Optional
from wtforms import StringField, IntegerField, SubmitField, TextAreaField, BooleanField, SelectField, FieldList, FormField, ValidationError, SelectMultipleField
import re


class ProductGroupForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    characteristic_id = SelectField('Группирующая характеристика', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Создать')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # загружаем список характеристик
        self.characteristic_id.choices = [(c.id, c.name) for c in Characteristic.query.all()]

class ColorForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    icon = FileField('Иконка')
    category_id = SelectField('Категория цвета', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Создать')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # загружаем список категорий цветов
        category_id_choices = [(c.id, c.name) for c in ColorCategory.query.all()]
        self.category_id.choices = [(0, 'Выберите категорию')] +  category_id_choices

class ColorCategoryForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    submit = SubmitField('Создать')

class TargetForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    submit = SubmitField('Создать')

class CharacteristicForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    submit = SubmitField('Создать характеристику')

class CategoryForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    parent_id = SelectField('Категория-родитель', coerce=int)
    children = SelectMultipleField('Категории-потомки', coerce=int)
    description_tag = TextAreaField('Описание', validators=[DataRequired()])
    submit = SubmitField('Создать категорию')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # загружаем список потомков
        children_choices = [(c.id, c.name) for c in Category.query.all()]
        self.children.choices = children_choices

        # список родителей
        parent_id_choices = [(c.id, c.name) for c in Category.query.all()]
        self.parent_id.choices = [(0, 'Выберите родительскую категорию')] + parent_id_choices


class ProductCharacteristicForm(FlaskForm):
    characteristic_id = SelectField('Характеристика', coerce=int, validators=[Optional()])
    value = StringField('Значение', validators=[DataRequired()])

class ProductPhotoForm(Form):
    photo = FileField('Фото')
    alt = StringField('Описание картинки alt', validators=[DataRequired()])
    num = IntegerField('Num')

    def validate_photo(form, field):
        if not field.data or not hasattr(field.data, 'filename') or field.data.filename == '':
            raise ValidationError('Файл не загружен')

        filename = field.data.filename

        if not re.match(r'^[a-zA-Z0-9.-]+$', filename):
            raise ValidationError('Название файла может содержать только английские буквы, цифры и дефис')

class ProductVideoForm(Form):
    video = FileField('Видео')
    num = IntegerField('Num')

    def validate_video(form, field):
        if not field.data or not hasattr(field.data, 'filename') or field.data.filename == '':
            raise ValidationError('Файл не загружен')

        filename = field.data.filename

        if not re.match(r'^[a-zA-Z0-9.-]+$', filename):
            raise ValidationError('Название файла может содержать только английские буквы, цифры и дефис')

class ProductForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    subname = StringField('Подназвание', validators=[Optional()])
    price = IntegerField('Цена', validators=[Optional()])
    description = TextAreaField('Описание', validators=[Optional()])
    application = TextAreaField('Применение', validators=[Optional()])
    is_new = BooleanField('Новинка')
    ozon_link = StringField('Ссылка Ozon', validators=[Optional()])
    wb_link = StringField('Ссылка Wildberries', validators=[Optional()])
    description_tag = TextAreaField('Описание', validators=[DataRequired()])
    weight = IntegerField('Вес (в граммах)', validators=[Optional()])

    characteristics = FieldList(FormField(ProductCharacteristicForm))
    categories = SelectMultipleField('Категории', coerce=int, validators=[DataRequired()])
    targets = SelectMultipleField('Что можно обрабатывать', coerce=int, validators=[Optional()])
    photos = FieldList(FormField(ProductPhotoForm), validators=[Optional()])
    videos = FieldList(FormField(ProductVideoForm), validators=[Optional()])

    group_id = SelectField('Группа товара', coerce=int, validators=[Optional()])
    color_id = SelectField('Цвет', coerce=int, validators=[Optional()])

    submit = SubmitField('Создать товар')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # загрузка характеристик
        characteristic_choices = [(c.id, c.name) for c in Characteristic.query.all()]
        for ind in range(len(self.characteristics)):
            self.characteristics[ind].characteristic_id.choices = characteristic_choices

        # загрузка категорий товаров
        category_choices = [(cat.id, cat.name) for cat in Category.query.all()]
        self.categories.choices = category_choices

        # загрузка таргетов
        targets_choices = [(target.id, target.name) for target in Target.query.all()]
        self.targets.choices = targets_choices
        
    def validate_characteristics(self, field):
        seen = set()
        for subform in field.entries:
            characteristic_id = subform.characteristic_id.data

            key = characteristic_id
            if key in seen:
                raise ValidationError(f'Характеристики дублируются')
            seen.add(key)

    def validate_group_id(self, field):
        seen = set()
        for subform in self.characteristics.entries:
            characteristic_id = subform.characteristic_id.data
            key = characteristic_id
            seen.add(key)

        group_char_map = {g.id: (g.characteristic_id or '') for g in ProductGroup.query.all()}
        if field.data in group_char_map.keys() and group_char_map[field.data] not in seen:
            raise ValidationError(f'У продукта нет характеристики, которая относится к выбранной группе')
import os

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form.upload import FileUploadField
from markupsafe import Markup

from models import db, Category, Car
import uuid

# Настройки загрузки изображений
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'cars')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class CarAdmin(ModelView):
    column_formatters = {
        'image': lambda v, c, m, p: Markup(f'<img src="/static/images/cars/{m.image}" height="50">') if m.image else ''
    }
    # Поля для отображения в списке
    column_list = ['model', 'price', 'category', 'in_stock']
    column_searchable_list = ['model']
    column_filters = ['price', 'in_stock']
    form_excluded_columns = ['images', 'brand_logo']
    form_columns = ['model', 'price', 'category', 'in_stock', 'image', 'description']

    # Форма редактирования
    form_extra_fields = {
        'image': FileUploadField(
            'Изображение',
            base_path=UPLOAD_FOLDER,
            namegen=lambda obj, file_data: f"{uuid.uuid4().hex}_{file_data.filename}",
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
        )
    }

    form_overrides = {
        'category': QuerySelectField
    }

    form_args = {
        'category': {
            'query_factory': lambda: db.session.query(Category).order_by(Category.name),
            'get_label': 'name',
            'allow_blank': False
        }
    }

    # Настройки страницы
    page_size = 20
    can_view_details = True
    can_export = True


def init_admin(app):
    admin = Admin(app, name='CN-Auto Admin', template_mode='bootstrap3')
    admin.add_view(CarAdmin(Car, db.session, category='Управление', name='Автомобили'))
    admin.add_view(ModelView(Category, db.session, category='Управление', name='Категории'))

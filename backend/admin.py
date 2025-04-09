from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from wtforms.fields import SelectField
from models import db, Category, Car
import os

# Настройки загрузки изображений
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'cars')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class CarAdmin(ModelView):
    # Поля для отображения в списке
    column_list = ['model', 'price', 'category', 'in_stock', 'is_electric']
    column_searchable_list = ['model']
    column_filters = ['price', 'in_stock']

    # Форма редактирования
    form_extra_fields = {
        'image': FileUploadField(
            'Изображение',
            base_path=UPLOAD_FOLDER,
            allowed_extensions=['jpg', 'jpeg', 'png']
        ),
        'category': SelectField(
            'Категория',
            choices=lambda: [(c.id, c.name) for c in Category.query.all()]
        )
    }

    # Настройки страницы
    page_size = 20
    can_view_details = True
    can_export = True

def init_admin(app):
    admin = Admin(app, name='CN-Auto Admin', template_mode='bootstrap3')
    admin.add_view(ModelView(Category, db.session, name='Категории'))
    admin.add_view(CarAdmin(Car, db.session, name='Автомобили'))
import os

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from wtforms.fields import SelectField

from backend.models import db, Car, Category, Brand, CarType

# Папка для изображений автомобилей
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'cars')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class CarAdmin(ModelView):
    column_list = ['model', 'price', 'brand_slug', 'car_type_slug', 'category', 'in_stock']
    column_searchable_list = ['model']
    column_filters = ['price', 'brand_slug', 'car_type_slug', 'in_stock']
    page_size = 20
    can_view_details = True
    can_export = True

    form_extra_fields = {
        'image': FileUploadField(
            'Изображение',
            base_path=UPLOAD_FOLDER,
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
        )
    }

    def scaffold_form(self):
        form_class = super().scaffold_form()

        form_class.brand_slug = SelectField('Бренд', choices=[])
        form_class.car_type_slug = SelectField('Тип', choices=[])

        return form_class

    def on_form_prefill(self, form, id):
        # Устанавливаем актуальные choices здесь
        form.brand_slug.choices = [(b.slug, b.name) for b in Brand.query.order_by(Brand.name)]
        form.car_type_slug.choices = [(t.slug, t.name) for t in CarType.query.order_by(CarType.name)]

    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.brand_slug.choices = [(b.slug, b.name) for b in Brand.query.order_by(Brand.name)]
        form.car_type_slug.choices = [(t.slug, t.name) for t in CarType.query.order_by(CarType.name)]
        return form


class CategoryAdmin(ModelView):
    column_list = ['name', 'slug']
    form_columns = ['name', 'slug', 'icon']


class BrandAdmin(ModelView):
    column_list = ['name', 'slug']
    form_columns = ['name', 'slug', 'logo']


class CarTypeAdmin(ModelView):
    column_list = ['name', 'slug']
    form_columns = ['name', 'slug', 'icon']


def init_admin(app):
    admin = Admin(app, name='CN-Auto Admin', template_mode='bootstrap3')
    admin.add_view(CarAdmin(Car, db.session, name='Автомобили'))
    admin.add_view(CategoryAdmin(Category, db.session, name='Категории'))
    admin.add_view(BrandAdmin(Brand, db.session, name='Бренды'))
    admin.add_view(CarTypeAdmin(CarType, db.session, name='Типы авто'))

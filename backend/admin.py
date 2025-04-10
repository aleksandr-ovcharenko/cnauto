import os

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form.upload import FileUploadField
from werkzeug.utils import secure_filename
from wtforms import MultipleFileField
from wtforms.fields import SelectField

from backend.models import db, Car, Category, Brand, CarType, Country

# Папка для изображений автомобилей
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'cars')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class CarAdmin(ModelView):
    column_list = ['model', 'price', 'year', 'mileage', 'engine', 'price_fob']
    column_searchable_list = ['model']
    column_filters = ['price', 'brand_slug', 'car_type_slug', 'in_stock']
    page_size = 20
    can_view_details = True
    can_export = True

    form_extra_fields = {
        'image': FileUploadField(
            'Главное изображение',
            base_path=UPLOAD_FOLDER,
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
        ),
        'images_upload': MultipleFileField('Галерея (несколько изображений)')
    }

    form_overrides = {
        'brand_slug': SelectField,
        'car_type_slug': SelectField,
    }

    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.brand_slug.choices = [
            (b.slug, b.name) for b in db.session.query(Brand).order_by(Brand.name).all()
        ]
        form.car_type_slug.choices = [
            (t.slug, t.name) for t in db.session.query(CarType).order_by(CarType.name).all()
        ]
        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        form.brand_slug.choices = [
            (b.slug, b.name) for b in db.session.query(Brand).order_by(Brand.name).all()
        ]
        form.car_type_slug.choices = [
            (t.slug, t.name) for t in db.session.query(CarType).order_by(CarType.name).all()
        ]
        return form

    def on_form_prefill(self, form, id):
        # Устанавливаем актуальные choices здесь
        form.brand_slug.choices = [(b.slug, b.name) for b in Brand.query.order_by(Brand.name)]
        form.car_type_slug.choices = [(t.slug, t.name) for t in CarType.query.order_by(CarType.name)]

    # def create_form(self, obj=None):
    #     form = super().create_form(obj)
    #     form.brand_slug.choices = [(b.slug, b.name) for b in Brand.query.order_by(Brand.name)]
    #     form.car_type_slug.choices = [(t.slug, t.name) for t in CarType.query.order_by(CarType.name)]
    #     return form

    form_columns = [
        'model', 'price', 'year', 'mileage', 'engine',
        'extras', 'price_fob',
        'image', 'images_upload',
        'category', 'brand_slug', 'car_type_slug',
        'description', 'in_stock'
    ]

    def on_model_change(self, form, model, is_created):
        if form.images_upload.data:
            saved_images = []
            for file in form.images_upload.data:
                if file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    saved_images.append(filename)

            # Сохраняем список файлов в JSON-поле
            if model.images:
                model.images += saved_images
            else:
                model.images = saved_images


class CategoryAdmin(ModelView):
    column_list = ['name', 'slug']
    form_columns = ['name', 'slug', 'icon']


class CountryAdmin(ModelView):
    column_list = ['id','name']
    form_columns = ['name']

    # Не показываем ID
    form_excluded_columns = ['id']


class BrandAdmin(ModelView):
    column_list = ['name', 'slug', 'logo', 'country']
    form_columns = ['name', 'slug', 'logo', 'country']
    column_searchable_list = ['name', 'slug']
    column_filters = ['country.name']

    can_export = True
    page_size = 30

    form_extra_fields = {
        'logo': FileUploadField(
            'Логотип',
            base_path=UPLOAD_FOLDER,
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
        ),
    }

    form_overrides = {
        'country': QuerySelectField
    }

    form_args = {
        'country': {
            'query_factory': lambda: db.session.query(Country).order_by(Country.name),
            'get_label': 'name',
            'allow_blank': True
        }
    }

    # def on_form_prefill(self, form, id):
    #     # Устанавливаем актуальные choices здесь
    #     form.country.choices = [(c.slug, c.name) for c in Category.query.order_by(Category.name)]
    #
    # def create_form(self, obj=None):
    #     form = super().create_form(obj)
    #     form.country.choices = [(c.slug, c.name) for c in Category.query.order_by(Category.name)]
    #     return form
    #
    # def edit_form(self, obj=None):
    #     form = super().edit_form(obj)
    #     form.country.choices = [
    #         (c.slug, c.name) for c in db.session.query(Category).order_by(Category.name).all()
    #     ]
    #
    #     return form


class CarTypeAdmin(ModelView):
    column_list = ['name', 'slug']
    form_columns = ['name', 'slug', 'icon']


def init_admin(app):
    admin = Admin(app, name='CN-Auto Admin', template_mode='bootstrap3')
    admin.add_view(CarAdmin(Car, db.session, name='Автомобили'))
    admin.add_view(CategoryAdmin(Category, db.session, name='Категории'))
    admin.add_view(BrandAdmin(Brand, db.session, name='Бренды'))
    admin.add_view(CarTypeAdmin(CarType, db.session, name='Типы авто'))
    admin.add_view(CountryAdmin(Country, db.session, name='Страны'))

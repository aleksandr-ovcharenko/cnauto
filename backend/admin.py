import os

from flask import flash, request, redirect, url_for
from flask_admin import Admin, expose
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from flask_admin.helpers import get_url
from markupsafe import Markup
from werkzeug.utils import secure_filename
from wtforms import MultipleFileField
from wtforms_sqlalchemy.fields import QuerySelectField

from backend.models import db, Car, Category, Brand, CarType, Country

# Папка для изображений автомобилей
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'cars')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class CarAdmin(ModelView):
    column_list = ['image_preview', 'model', 'price', 'brand_preview', 'car_type']
    column_labels = {'image_preview': 'Фото', 'brand_preview': 'Бренд'}

    column_searchable_list = ['model']
    column_filters = ['price', 'car_type', 'in_stock']
    page_size = 20
    can_view_details = True
    can_export = True
    column_display_pk = True

    def _image_preview(view, context, model, name):
        if model.image:
            return Markup(f'<img src="{get_url("static", filename="images/cars/" + model.image)}" height="60">')
        return ''

    def _brand_preview(view, context, model, name):
        if model.brand and model.brand.logo:
            return Markup(f'<img src="{get_url("static", filename="images/brands/" + model.brand.logo)}" height="60">'
                          f'</br>{model.brand.name}')
        elif model.brand:
            return model.brand.name  # показать просто название бренда
        return '—'

    column_formatters = {
        'image_preview': _image_preview,
        'brand_preview': _brand_preview
    }

    form_extra_fields = {
        'image': FileUploadField(
            'Главное изображение',
            base_path=os.path.join(os.path.dirname(__file__), 'static', 'images', 'cars'),
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
        ),
        'images_upload': MultipleFileField('Галерея (несколько изображений)')
    }

    form_overrides = {
        'brand': QuerySelectField,
        'car_type': QuerySelectField,
    }

    edit_template = 'admin/edit_with_nav.html'  # кастомный шаблон

    def _get_adjacent_ids(self, model_id):
        all_ids = [car.id for car in Car.query.order_by(Car.id).all()]
        try:
            idx = all_ids.index(model_id)
        except ValueError:
            return None, None

        prev_id = all_ids[idx - 1] if idx > 0 else None
        next_id = all_ids[idx + 1] if idx < len(all_ids) - 1 else None
        return prev_id, next_id

    def render(self, template, **kwargs):
        if template == self.edit_template:
            model_id = request.args.get('id', type=int)
            prev_id, next_id = self._get_adjacent_ids(model_id)
            kwargs.update({'prev_id': prev_id, 'next_id': next_id})
        return super().render(template, **kwargs)

    form_columns = ['model', 'price', 'brand', 'car_type', 'image', 'images_upload', 'description', 'year', 'mileage',
                    'engine', 'in_stock']

    form_args = {
        'brand': {
            'query_factory': lambda: db.session.query(Brand).order_by(Brand.name),
            'get_label': 'name'
        },
        'car_type': {
            'query_factory': lambda: db.session.query(CarType).order_by(CarType.name),
            'get_label': 'name'
        }
    }

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

    # ===============================
    # Copy current car into new
    # ===============================
    @expose('/duplicate/<int:id>')
    def duplicate_view(self, id):
        car = Car.query.get_or_404(id)

        new_car = Car(
            model=car.model + " (копия)",
            price=car.price,
            image=car.image,
            brand=car.brand,
            car_type=car.car_type,
            in_stock=car.in_stock,
            description=car.description,
            year=car.year,
            mileage=car.mileage,
            engine=car.engine,
        )
        db.session.add(new_car)
        db.session.commit()

        flash(f'✅ Автомобиль "{new_car.model}" скопирован.', 'success')
        return redirect(url_for('.edit_view', id=new_car.id))

    @action('duplicate', 'Копировать', 'Вы уверены, что хотите скопировать выбранные авто?')
    def action_duplicate(self, ids):
        try:
            for car_id in ids:
                car = Car.query.get(car_id)
                if not car:
                    continue

                # Создаём копию
                new_car = Car(
                    model=car.model + " (копия)",
                    price=car.price,
                    image=car.image,
                    brand=car.brand,
                    car_type=car.car_type,
                    in_stock=car.in_stock,
                    description=car.description,
                    year=car.year,
                    mileage=car.mileage,
                    engine=car.engine
                )
                db.session.add(new_car)

            db.session.commit()
            flash(f"✅ Успешно скопировано: {len(ids)} авто.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Ошибка при копировании: {e}", "error")


class CategoryAdmin(ModelView):
    column_list = ['name', 'slug']
    form_columns = ['name', 'slug', 'icon']


class CountryAdmin(ModelView):
    column_list = ['id', 'name']
    form_columns = ['name']

    # Не показываем ID
    form_excluded_columns = ['id']


class BrandAdmin(ModelView):
    column_list = ['logo_preview', 'name', 'slug', 'country']
    column_labels = {'logo_preview': 'Логотип'}

    form_columns = ['name', 'slug', 'logo', 'country']
    column_searchable_list = ['name', 'slug']
    column_filters = ['country.name']

    can_export = True
    page_size = 30

    def _logo_preview(view, context, model, name):
        if model.logo:
            return Markup(f'<img src="{get_url("static", filename="images/brands/" + model.logo)}" height="30">')
        return ''

    column_formatters = {
        'logo_preview': _logo_preview
    }

    form_extra_fields = {
        'logo': FileUploadField(
            'Логотип',
            base_path=os.path.join(os.path.dirname(__file__), 'static', 'images', 'brands'),
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

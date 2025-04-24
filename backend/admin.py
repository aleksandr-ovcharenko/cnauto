import logging
import os

# Add the directory to the path for relative imports
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import flash, request, redirect, url_for
from flask_admin import Admin, expose, BaseView
from flask_admin import AdminIndexView
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.form.upload import FileUploadField
from flask_admin.helpers import get_url
from flask_admin.model.form import InlineFormAdmin
from flask_login import current_user
from markupsafe import Markup
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.security import generate_password_hash
from wtforms import PasswordField
from wtforms.fields import HiddenField
from wtforms.fields.simple import FileField, MultipleFileField
from wtforms.widgets.core import HiddenInput
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField

from models import Role, User, CarImage, BrandSynonym, Currency, CarType
from models import db, Car, Category, Brand, Country

# Папка для изображений автомобилей
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'cars')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    def render(self, template, **kwargs):
        kwargs['current_user'] = current_user
        return super().render(template, **kwargs)

    @expose('/')
    def index(self):
        return self.render('admin/custom_admin_base.html')


class SecureModelView(ModelView):
    base_template = 'admin/custom_admin_base.html'

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login', next=request.url))

    def render(self, template, **kwargs):
        kwargs['current_user'] = current_user
        return super().render(template, **kwargs)


class UserAdmin(SecureModelView):
    column_list = ['username', 'email', 'roles']
    column_searchable_list = ['username', 'email']
    column_filters = ['roles.name']
    column_labels = {
        'username': 'Имя пользователя',
        'email': 'Email',
        'roles': 'Роли'
    }
    column_formatters = {
        'roles': lambda v, c, m, p: ', '.join([r.name for r in m.roles]) if m.roles else '—'
    }

    form_columns = ['username', 'email', 'password', 'roles']
    form_extra_fields = {
        'password': PasswordField('Пароль (оставьте пустым, если не менять)')
    }

    form_overrides = {
        'roles': QuerySelectMultipleField
    }

    form_args = {
        'roles': {
            'query_factory': lambda: db.session.query(Role).order_by(Role.name),
            'get_label': 'name'
        }
    }

    def on_model_change(self, form, model, is_created):
        print(">> Сработал on_model_change", form.password.data)
        if form.password.data:
            model.password_hash = generate_password_hash(form.password.data, method='pbkdf2:sha256')

    column_exclude_list = ['password_hash']

    @expose('/duplicate/<int:id>')
    def duplicate_view(self, id):
        user = User.query.get_or_404(id)

        new_user = User(
            username=user.username + "_copy",
            email=user.email + "_copy@example.com",
            password_hash=generate_password_hash("newpassword123", method='pbkdf2:sha256'),
            roles=user.roles[:]  # копируем список ролей
        )
        db.session.add(new_user)
        db.session.commit()

        flash(f'✅ Пользователь "{new_user.username}" скопирован. Пароль: newpassword123', 'success')
        return redirect(url_for('.edit_view', id=new_user.id))

    @action('duplicate', 'Копировать', 'Вы уверены, что хотите скопировать выбранных пользователей?')
    def action_duplicate(self, ids):
        for user_id in ids:
            user = User.query.get(user_id)
            if not user:
                continue
            new_user = User(
                username=user.username + "_copy",
                email=user.email + "_copy@example.com",
                password_hash=generate_password_hash("newpassword123", method='pbkdf2:sha256'),
                roles=user.roles[:]
            )
            db.session.add(new_user)
        db.session.commit()
        flash(f'✅ Скопировано: {len(ids)} пользователей. Пароль у всех: newpassword123', 'success')


class CarImageAdmin(SecureModelView):
    column_list = ['preview', 'car', 'title', 'alt', 'position']
    form_columns = ['car', 'url', 'title', 'alt', 'position']

    def _preview(view, context, model, name):
        return Markup(f'<img src="{model.url}" height="50">') if model.url else ''

    column_formatters = {'preview': _preview}

    form_extra_fields = {
        'file_upload': FileField('Загрузить изображение')
    }

    def on_model_change(self, form, model, is_created):
        file = form.file_upload.data
        if file:
            from utils.cloudinary_upload import upload_image
            uploaded_url = upload_image(file, car_id=model.car_id, car_name=model.car.model)
            if uploaded_url:
                model.url = uploaded_url


class CarAdmin(SecureModelView):
    base_template = 'admin/custom_admin_base.html'
    list_template = 'admin/model/list.html'

    column_list = ['image_preview', 'brand_preview', 'model', 'price', 'currency', 'car_type']
    column_labels = {'image_preview': 'Фото', 'brand_preview': 'Бренд', 'currency': 'Валюта'}

    column_searchable_list = ['model']
    column_filters = ['price', 'car_type', 'in_stock']
    page_size = 20
    can_view_details = True
    can_export = True
    column_display_pk = True
    can_delete = True
    can_create = True
    can_edit = True

    action_disallowed_list = []
    column_display_actions = True

    def _image_preview(view, context, model, name):
        if model.image_url:
            return Markup(f'<img src="{model.image_url}" height="60">')
        return ''

    def _brand_preview(view, context, model, name):
        if model.brand and model.brand.logo:
            return Markup(f'<img src="{get_url("static", filename="images/brands/" + model.brand.logo)}" height="60">'
                          f'</br>{model.brand.name}')
        elif model.brand:
            return model.brand.name  # показать просто название бренда
        return '—'

    def _currency_display(view, context, model, name):
        if model.currency:
            return f"{model.currency.code} ({model.currency.symbol})"
        return '—'

    def _price_formatter(view, context, model, name):
        from app import format_currency_filter

        # Use the same format_currency_filter we created for the templates
        # This ensures consistent formatting across admin and frontend
        formatted_price = format_currency_filter(model.price, model.currency)

        # No data attributes needed - pure server-side formatting
        return Markup(f'<span class="price">{formatted_price}</span>')

    column_formatters = {
        'image_preview': _image_preview,
        'brand_preview': _brand_preview,
        'currency': _currency_display,
        'price': _price_formatter
    }

    form_extra_fields = {
        'image_upload': FileField(
            'Главное изображение'
        ),
        'images_upload': MultipleFileField('Галерея (несколько изображений)', widget=HiddenInput())

    }

    def on_model_change(self, form, model, is_created):
        print(f"🧾 Обработка формы: {model.brand.name} {model.model} (ID: {model.id})")
        from utils.cloudinary_upload import upload_image

        # Главное изображение
        image_file = form.image_upload.data
        if image_file and image_file.filename:
            print(f"📎 Загрузка главного изображения: {image_file.filename}")
            uploaded_url = upload_image(image_file, car_id=model.id, car_name=model.model, is_main=True)
            if uploaded_url:
                model.image_url = uploaded_url
                print(f"✅ Главная картинка загружена: {uploaded_url}")
            else:
                print("⚠️ Не удалось загрузить главное изображение")

        # Галерея изображений — безопасная проверка
        if hasattr(form, 'images_upload') and form.images_upload.data:
            gallery_files = form.images_upload.data
            print("📚 Обработка галереи")
            saved_images = []
            for i, file in enumerate(gallery_files):
                if file and file.filename:
                    print(f"📷 Галерея {i + 1}: {file.filename}")
                    uploaded_url = upload_image(file, car_id=model.id, car_name=model.model, is_main=False, index=i + 1)
                    if uploaded_url:
                        saved_images.append(uploaded_url)
                        print(f"✅ Загружено: {uploaded_url}")
                    else:
                        print("⚠️ Не удалось загрузить:", file.filename)

            if saved_images:
                if not isinstance(model.images, list):
                    model.images = []
                model.images += saved_images
                flag_modified(model, "images")  # 💡 без этого SQLAlchemy может не зафиксировать изменение
                print(f"✅ Добавлено: {saved_images} к: {model.images}")

    form_overrides = {
        'brand': QuerySelectField,
        'car_type': QuerySelectField,
        'currency': QuerySelectField
    }

    form_columns = [
        'model', 'price', 'currency', 'brand', 'car_type',
        'image_upload',
        'description', 'year', 'mileage', 'engine', 'in_stock'
    ]

    form_args = {
        'brand': {
            'query_factory': lambda: db.session.query(Brand).order_by(Brand.name),
            'get_label': 'name'
        },
        'car_type': {
            'query_factory': lambda: db.session.query(CarType).order_by(CarType.name),
            'get_label': 'name'
        },
        'currency': {
            'query_factory': lambda: db.session.query(Currency).order_by(Currency.code),
            'get_label': lambda c: f"{c.code} ({c.symbol})"
        },
        # --- FIXED: Example for SelectField with choices ---
        # 'example_field': {
        #     'choices': [('value1', 'Label 1'), ('value2', 'Label 2')],  # Always a list of tuples
        # },
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

    # ===============================
    # Copy current car into new
    # ===============================
    @expose('/duplicate/<int:id>')
    def duplicate_view(self, id):
        car = Car.query.get_or_404(id)

        new_car = Car(
            model=car.model + " (копия)",
            price=car.price,
            image_url=car.car.image_url,
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
                    image_url=car.image_url,
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

    @expose('/generate_from_gallery/<int:id>', methods=['POST'])
    def generate_from_gallery(self, id):
        from utils.telegram_import import generate_image
        image = CarImage.query.get_or_404(id)
        car = image.car

        prompt = (
            f"Professional car studio shot, clean background, only the car visible. "
            f"Car: {car.model}-{car.brand.name}, fully isolated, no other objects or cars. "
            "License plate must clearly show 'cncars.ru'. "
            "Car positioned diagonally: front facing left, rear facing right. "
            "Clean, sharp details, high-quality render, studio lighting. "
            "Remove all background elements, shadows, and distractions. "
            "The car should look like a perfect 3D model on a white background."
        )

        try:
            new_image = generate_image(mode="photon", prompt=prompt, image_url=car.gallery_images[0].url,
                                       car_model=car.model, car_brand=car.brand, car_id=car.id)
            if new_image:
                car.image_url = new_image
                db.session.commit()
            else:
                flash(f"❌ Не удалось сгенерировать для {car.model}", "error")
        except Exception as e:
            flash(f"❌ Ошибка при генерации изображения: {e}", "error")

        flash(f"✅ Изображение успешно обновлено!", "success")

        return redirect(url_for('.edit_view', id=image.car.id))

    @expose('/edit_gallery/<int:id>', methods=['POST'])
    def edit_gallery(self, id):
        car = Car.query.get_or_404(id)
        ids_in_order = request.form.get('order', '').split(',')
        updated_ids = set()

        for img in car.gallery_images:
            str_id = str(img.id)
        print(f"🔍 Обрабатываем img.id={str_id}")
        print("📥 request.form:", dict(request.form))

        if f"title_{str_id}" in request.form or f"alt_{str_id}" in request.form:
            print("✅ Нашли в форме")
            img.title = request.form.get(f"title_{str_id}")
            img.alt = request.form.get(f"alt_{str_id}")
            if str_id in ids_in_order:
                img.position = ids_in_order.index(str_id)
            updated_ids.add(str_id)

        db.session.commit()
        flash("✅ Галерея обновлена", "success")
        return redirect(url_for('.edit_view', id=car.id))

    @expose('/upload_gallery/<int:id>', methods=['POST'])
    def upload_gallery(self, id):
        car = Car.query.get_or_404(id)
        from utils.cloudinary_upload import upload_image

        files = request.files.getlist('new_images')
        for i, file in enumerate(files):
            if file and file.filename:
                url = upload_image(file, car_id=car.id, car_name=car.model, is_main=False, index=i)
                if url:
                    image = CarImage(car_id=car.id, url=url, position=len(car.gallery_images) + i)
                    db.session.add(image)

        db.session.commit()
        flash("✅ Новые изображения загружены", "success")
        return redirect(url_for('.edit_view', id=car.id))

    @expose('/car-image/delete/<int:id>', methods=['POST'])
    def delete_image(self, id):
        image = CarImage.query.get_or_404(id)
        db.session.delete(image)
        db.session.commit()
        return "OK"

    def create_form(self, obj=None):
        form = super().create_form(obj)
        self._inject_gallery_button(form)
        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        self._inject_gallery_button(form)
        return form

    def _inject_gallery_button(self, form):
        from wtforms.fields import Field
        from markupsafe import Markup

        class GalleryButton(Field):
            def __init__(self, label='', **kwargs):
                super().__init__(label, **kwargs)
                self.widget = lambda field, **kwargs: Markup('''
                    <div class="form-group d-flex align-items-center justify-content-between mb-3" style="min-height: 40px; border: 1px dashed red; padding: 5px 10px;">
                        <label style="font-weight: 500; margin: 0;">Галерея</label>
                        <button type="button" class="btn btn-outline-secondary btn-sm"
                                data-toggle="modal" data-target="#galleryModal">
                            🖼 Управление
                        </button>
                    </div>
                ''')

        setattr(form, 'gallery_button', GalleryButton())

        # Определим порядок полей вручную
        if hasattr(form, '_fields'):
            fields = list(form._fields.keys())
            if 'gallery_button' not in fields and 'image_upload' in fields:
                fields.insert(fields.index('image_upload') + 1, 'gallery_button')
                # Перестроим OrderedDict
                from collections import OrderedDict
                form._fields = OrderedDict((f, form._fields[f]) for f in fields if f in form._fields)


class CategoryAdmin(SecureModelView):
    column_list = ['name', 'slug']
    form_columns = ['name', 'slug', 'icon']


class CountryAdmin(SecureModelView):
    column_list = ['id', 'name']
    form_columns = ['name']

    # Не показываем ID
    form_excluded_columns = ['id']


class BrandAdmin(SecureModelView):
    column_list = ['logo_preview', 'name', 'slug', 'country']
    column_labels = {'logo_preview': 'Логотип'}
    
    # Fixed implementation of inline_models that avoids the tuple error
    # Each item must be a proper model class or a dict with configuration
    inline_models = [BrandSynonym]  # This is a list with one class, not a tuple
    
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
        )
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


class CarTypeAdmin(SecureModelView):
    column_list = ['icon_preview', 'name', 'slug']
    column_labels = {'icon_preview': 'Иконка'}
    form_columns = ['name', 'slug', 'icon']

    def _icon_preview(view, context, model, name):
        if model.icon:
            return Markup(f'<img src="{get_url("static", filename="images/types/" + model.icon)}" height="30">')
        return ''

    column_formatters = {
        'icon_preview': _icon_preview
    }

    form_extra_fields = {
        'icon': FileUploadField(
            'Иконка',
            base_path=os.path.join(os.path.dirname(__file__), 'static', 'images', 'types'),
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
        ),
    }


class CurrencyAdmin(SecureModelView):
    column_list = ('id', 'code', 'name', 'symbol', 'locale')
    column_searchable_list = ('code', 'name', 'symbol', 'locale')
    form_columns = ('code', 'name', 'symbol', 'locale')
    column_sortable_list = ('id', 'code', 'name', 'locale')


def init_admin(app):
    admin = Admin(
        app,
        name='CN-Auto Admin',
        template_mode='bootstrap3',
        index_view=SecureAdminIndexView()
    )

    @app.context_processor
    def admin_context():
        return dict(current_user=current_user)

    # Add API Docs link to admin
    class ApiDocsView(BaseView):
        @expose('/')
        def index(self):
            return redirect(url_for('api_docs'))
    
    # Add Logs view link
    class LogsView(BaseView):
        @expose('/')
        def index(self):
            return redirect(url_for('view_logs'))
    
    admin.add_view(CarImageAdmin(CarImage, db.session, name='Фото машин'))
    admin.add_view(CarAdmin(Car, db.session, name='Автомобили'))
    admin.add_view(CategoryAdmin(Category, db.session, name='Категории'))
    admin.add_view(BrandAdmin(Brand, db.session, name='Марки'))
    admin.add_view(CountryAdmin(Country, db.session, name='Страны'))
    admin.add_view(UserAdmin(User, db.session, name='Пользователи'))
    admin.add_view(CarTypeAdmin(CarType, db.session, name='Типы авто'))
    admin.add_view(CurrencyAdmin(Currency, db.session, name='Currencies'))
    
    # Add tool views
    admin.add_view(ApiDocsView(name='API Документация', category='Инструменты'))
    admin.add_view(LogsView(name='Логи', category='Инструменты'))

    return admin

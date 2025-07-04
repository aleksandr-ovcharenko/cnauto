import logging
import os
from datetime import datetime

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
from flask_login import current_user
from markupsafe import Markup
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.security import generate_password_hash
from wtforms import PasswordField
from wtforms.fields.simple import FileField, MultipleFileField
from wtforms.widgets.core import HiddenInput
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField

# Update imports to use relative imports consistently
from .models import Role, User, CarImage, BrandSynonym, Currency, CarType, ImageTask
from .models import db, Car, Category, Brand, Country

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
        logging.getLogger(__name__).info(f'✅ Пользователь "{new_user.username}" скопирован. Пароль: newpassword123')
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
        logging.getLogger(__name__).info(f'✅ Скопировано: {len(ids)} пользователей. Пароль у всех: newpassword123')


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
            try:
                from backend.utils.cloudinary_upload import upload_image
            except ImportError:
                from utils.cloudinary_upload import upload_image
            uploaded_url = upload_image(file, car_id=model.car_id, car_name=model.car.model, car_brand=model.car.brand.name if model.car.brand else None)
            if uploaded_url:
                model.url = uploaded_url


class CarAdmin(SecureModelView):
    base_template = 'admin/custom_admin_base.html'
    list_template = 'admin/model/list.html'

    column_list = ['image_preview', 'brand_preview', 'model', 'modification', 'trim', 'price', 'currency', 'car_type']
    column_labels = {'image_preview': 'Фото', 'brand_preview': 'Бренд', 'currency': 'Валюта',
                     'modification': 'Модификация', 'trim': 'Комплектация'}

    column_searchable_list = ['model', 'modification', 'trim']
    column_filters = ['price', 'car_type', 'in_stock', 'modification', 'trim']
    page_size = 20
    can_view_details = True
    can_export = True
    column_display_pk = True
    can_delete = True
    can_create = True
    can_edit = True
    
    # Sort by ID in descending order (newest first)
    column_default_sort = ('id', True)  # (column, descending)

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
        try:
            from backend import format_currency_filter
        except ImportError:
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
        logger = logging.getLogger(__name__)
        logger.info(f"🧾 Обработка формы: {model.brand.name} {model.model} (ID: {model.id})")
        try:
            from backend.utils.cloudinary_upload import upload_image
        except ImportError:
            from utils.cloudinary_upload import upload_image

        # Block car creation without brand and model
        if is_created:
            if not model.brand or not model.model or not str(model.model).strip():
                raise ValueError("Нельзя создать автомобиль без бренда и модели.")

        # Главное изображение
        image_file = form.image_upload.data
        if image_file and image_file.filename:
            logger.info(f"📎 Загрузка главного изображения: {image_file.filename}")
            uploaded_url = upload_image(image_file, car_id=model.id, car_name=model.model, car_brand=model.brand.name if model.brand else None, is_main=True)
            if uploaded_url:
                model.image_url = uploaded_url
                logger.info(f"✅ Главная картинка загружена: {uploaded_url}")
            else:
                logger.warning("⚠️ Не удалось загрузить главное изображение")

        # Галерея изображений — безопасная проверка
        if hasattr(form, 'images_upload') and form.images_upload.data:
            gallery_files = form.images_upload.data
            logger.info("📚 Обработка галереи")
            saved_images = []
            for i, file in enumerate(gallery_files):
                if file and file.filename:
                    logger.info(f"📷 Галерея {i + 1}: {file.filename}")
                    uploaded_url = upload_image(file, car_id=model.id, car_name=model.model, car_brand=model.brand.name if model.brand else None, is_main=False, index=i + 1)
                    if uploaded_url:
                        saved_images.append(uploaded_url)
                        logger.info(f"✅ Загружено: {uploaded_url}")
                    else:
                        logger.warning(f"⚠️ Не удалось загрузить: {file.filename}")

            if saved_images:
                if not isinstance(model.images, list):
                    model.images = []
                model.images += saved_images
                flag_modified(model, "images")  # 💡 без этого SQLAlchemy может не зафиксировать изменение
                logger.info(f"✅ Добавлено: {saved_images} к: {model.images}")

    form_overrides = {
        'brand': QuerySelectField,
        'car_type': QuerySelectField,
        'currency': QuerySelectField
    }

    form_columns = [
        'model', 'modification', 'trim', 'price', 'currency', 'brand', 'car_type',
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
            currency=car.currency  # <-- copy currency
        )
        db.session.add(new_car)
        db.session.commit()

        flash(f'✅ Автомобиль "{new_car.model}" скопирован.', 'success')
        logging.getLogger(__name__).info(f'✅ Автомобиль "{new_car.model}" скопирован.')
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
                    engine=car.engine,
                    currency=car.currency  # <-- copy currency
                )
                db.session.add(new_car)

            db.session.commit()
            flash(f"✅ Успешно скопировано: {len(ids)} авто.", "success")
            logging.getLogger(__name__).info(f"✅ Успешно скопировано: {len(ids)} авто.")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Ошибка при копировании: {e}", "error")
            logging.getLogger(__name__).error(f"❌ Ошибка при копировании: {e}")

    @expose('/generate_from_gallery/<int:id>', methods=['POST'])
    def generate_from_gallery(self, id):
        """Generate a new image from a gallery image using AI."""
        import logging
        try:
            from backend.utils.file_logger import get_module_logger
        except ImportError:
            from utils.file_logger import get_module_logger
        try:
            from backend.models import ImageTask
        except ImportError:
            from models import ImageTask
        logger = get_module_logger(__name__)

        # Get the gallery image by ID
        image = CarImage.query.get_or_404(id)
        car = image.car
        logger.info(f"🔍 Starting AI image generation for car ID={car.id} from image ID={id}")

        # Create a new ImageTask record with a unique task_id
        import time
        task_id = f"img_task_{car.id}_{int(time.time())}"
        
        image_task = ImageTask(
            task_id=task_id,
            car_id=car.id,
            source='gallery_ai',
            status='processing',
            source_image_id=image.id,
            source_url=image.url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(image_task)
        db.session.commit()
        logger.info(f"📝 Created ImageTask record #{image_task.id} for car ID={car.id}")

        try:
            # Get the prompt from the image or car information
            prompt_hint = (
                "Professional car studio shot, ultra-clean pure white background, only the car visible with ample empty space around it. "
                f"Car: {car.brand.name if car.brand else 'Unknown'} {car.model}, perfectly isolated with at least 2 meters of empty space on all sides, no other objects or cars visible. "
                "License plate must clearly and legibly display 'cncars.ru' in proper format. "
                f"Car positioned diagonally in frame: front facing 30 degrees left, rear facing 30 degrees right, with slight perspective as if viewed from eye level. "
                "The car should be positioned not too close - about 5-7 meters from the virtual camera, showing full body with space around. "
                "Crisp, ultra-sharp details, 8K quality render, professional three-point studio lighting with soft shadows. "
                "Absolutely no background elements, no reflections of surroundings, no stray shadows - only clean, pure white backdrop. "
                "The car should appear as a flawless 3D model with perfect proportions, slightly matte surface to avoid glare. "
                "Add subtle ambient occlusion shadows under the car for natural grounding effect."
            )
            logger.info(f"🔤 Using detailed prompt: '{prompt_hint}'")

            # Call the image generation function
            try:
                from backend.utils.generator_photon import generate_with_photon
            except ImportError:
                from utils.generator_photon import generate_with_photon
            logger.info(f"🚀 Calling Photon generator with image URL: {image.url}")

            # Image lookup and generation process
            new_image_url = generate_with_photon(
                prompt=prompt_hint,
                image_url=image.url,
                car_model=car.model,
                car_brand=car.brand.name if car.brand else "Unknown",
                car_id=car.id
            )

            # Update the task with the status
            if new_image_url:
                logger.info(f"✅ Successfully generated image, URL: {new_image_url}")

                # Create a new gallery image with the generated image
                new_image = CarImage(
                    car_id=car.id,
                    url=new_image_url,
                    title=f"AI Generated {datetime.now().strftime('%Y-%m-%d')}",
                    alt=f"AI generated {car.brand.name if car.brand else ''} {car.model}",
                    position=(len(car.gallery_images) if car.gallery_images else 0)
                )
                db.session.add(new_image)
                db.session.flush()  # Get the new ID without committing

                # Set as main image
                car.image_url = new_image_url
                
                # Update the image task status
                image_task.status = 'completed'
                image_task.result_url = new_image_url
                image_task.completed_at = datetime.now()
                
                # Commit all changes atomically
                try:
                    db.session.commit()
                    logger.info(f"✅ Gallery image and car main image updated successfully, ID={new_image.id}")
                    
                    # Double-check that our changes were saved
                    db.session.refresh(car)
                    if car.image_url != new_image_url:
                        logger.warning(f"⚠️ Car image URL not updated correctly: {car.image_url} vs {new_image_url}")
                        # Force update
                        car.image_url = new_image_url
                        db.session.commit()
                        logger.info(f"🔄 Forced update of car.image_url: {car.image_url}")
                        
                    return redirect(url_for('car.edit_view', id=car.id))
                except Exception as db_error:
                    logger.error(f"❌ Database error saving gallery image: {str(db_error)}")
                    db.session.rollback()
                    flash(f"Сохранено, но произошла ошибка при сохранении изображения: {str(db_error)[:100]}", "error")
                    return redirect(url_for('car.edit_view', id=car.id))
            else:
                # Log failure but the URL was generated successfully in Replicate
                # This is likely a validation error in our code
                from utils.image_queue import add_to_generated_cache
                
                # Check logs for generated URL to try to recover it
                try:
                    import re
                    import os
                    from flask import current_app
                    
                    # Try several possible log file locations
                    log_paths = [
                        # Try app log path from config if available
                        current_app.config.get('LOG_FILE_PATH'),
                        # Try common deployment locations
                        "/app/backend/logs/app.log",
                        "/app/logs/app.log",
                        # Try with date if available
                        f"/app/backend/logs/app_{datetime.now().strftime('%Y%m%d')}.log",
                        # Try development path as last resort
                        "/home/aleks/dev/cnauto-site/backend/logs/app.log",
                        f"/home/aleks/dev/cnauto-site/backend/logs/app_{datetime.now().strftime('%Y%m%d')}.log",
                    ]
                    
                    # Filter out None values
                    log_paths = [path for path in log_paths if path]
                    
                    log_content = ""
                    for log_path in log_paths:
                        if os.path.exists(log_path):
                            logger.info(f"📁 Found log file at: {log_path}")
                            with open(log_path, "r") as f:
                                log_content = f.read()
                                break
                    
                    if not log_content:
                        logger.warning("⚠️ Could not find any log files to extract URLs from")
                    else:
                        match = re.search(f"Downloading generated image from: (https?://.*?)\\n", log_content)
                        if match:
                            generator_output_url = match.group(1)
                            logger.info(f"🔍 Extracted generated image URL from logs: {generator_output_url}")
                            # Save for later retry
                            add_to_generated_cache(f"admin-car-{car.id}-img-{id}", generator_output_url)
                            logger.info(f"💾 Cached generated URL for later retry: {generator_output_url}")
                            
                            # Update task status
                            image_task.status = 'waiting_upload'
                            image_task.error = 'Upload failed but generation succeeded'
                            image_task.notes = generator_output_url
                            db.session.commit()
                            
                            flash("Изображение было сгенерировано, но произошла ошибка при загрузке. Мы сохранили ссылку для повторной попытки.", "warning")
                            return redirect(url_for('car.edit_view', id=car.id))
                except Exception as log_error:
                    logger.error(f"❌ Failed to extract URL from logs: {str(log_error)}")
                
                logger.warning(f"⚠️ AI generation returned None but no exception was raised. Car ID={car.id}, Image ID={id}")
                image_task.status = 'failed'
                image_task.error = 'Generation returned None'
                db.session.commit()

                logger.error(f"❌ Не удалось сгенерировать изображение для {car.model}. Проверьте логи для деталей.")
                flash(f"Не удалось сгенерировать изображение для {car.model}. Проверьте логи для деталей.", "error")
                logger.warning(f"⚠️ AI image generation failed for car {car.id} - no image returned")
                return redirect(url_for('car.edit_view', id=car.id))
        except Exception as e:
            # Update the task with the error
            image_task.status = 'failed'
            image_task.error = str(e)
            db.session.commit()

            logger.error(f"❌ AI generation exception: {str(e)}")
            logger.error(f"❌ Exception details:", exc_info=True)
            flash(f"❌ Ошибка при генерации изображения: {e}", "error")
            logging.getLogger(__name__).error(f"❌ Ошибка при генерации изображения: {e}")

        logger.info(f"🔙 Redirecting user to car edit view for car ID={car.id}")
        return redirect(url_for('car.edit_view', id=car.id))

    @expose('/edit_gallery/<int:id>', methods=['POST'])
    def edit_gallery(self, id):
        import logging
        try:
            from backend.utils.file_logger import get_module_logger
        except ImportError:
            from utils.file_logger import get_module_logger
        logger = get_module_logger(__name__)
        car = Car.query.get_or_404(id)
        ids_in_order = request.form.get('order', '').split(',')

        # Extract all possible image IDs from the form
        form_img_ids = {key.split('_')[1] for key in request.form.keys()
                        if key.startswith(('title_', 'alt_', 'position_'))}

        logger.info(f"🖼 Обновление галереи для car_id={id}, найдено {len(form_img_ids)} изображений в форме")
        updated_ids = set()

        for img in car.gallery_images:
            str_id = str(img.id)

            # Skip images that aren't in the form
            if str_id not in form_img_ids:
                continue

            # Only process images where values are actually specified
            if f"title_{str_id}" in request.form or f"alt_{str_id}" in request.form:
                # Log only once for each image, not for each field
                logger.info(f"✏️ Обновляем данные для изображения id={str_id}")

                # Only set fields that are actually present in the form
                if f"title_{str_id}" in request.form:
                    img.title = request.form.get(f"title_{str_id}")
                if f"alt_{str_id}" in request.form:
                    img.alt = request.form.get(f"alt_{str_id}")

                # Set position if available
                if str_id in ids_in_order:
                    img.position = ids_in_order.index(str_id)

                updated_ids.add(str_id)

        db.session.commit()
        logger.info(f"✅ Галерея обновлена для car_id={id}, обработано {len(updated_ids)} изображений")
        flash("✅ Галерея обновлена", "success")
        logging.getLogger(__name__).info("✅ Галерея обновлена")
        return redirect(url_for('car.edit_view', id=car.id))

    @expose('/upload_gallery/<int:id>', methods=['POST'])
    def upload_gallery(self, id):
        car = Car.query.get_or_404(id)
        try:
            from backend.utils.cloudinary_upload import upload_image
        except ImportError:
            from utils.cloudinary_upload import upload_image
        files = request.files.getlist('new_images')
        for i, file in enumerate(files):
            if file and file.filename:
                url = upload_image(file, car_id=car.id, car_name=car.model, car_brand=car.brand.name if car.brand else None, is_main=False, index=i + 1)
                if url:
                    image = CarImage(car_id=car.id, url=url, position=len(car.gallery_images) + i)
                    db.session.add(image)

        db.session.commit()
        flash("✅ Новые изображения загружены", "success")
        logging.getLogger(__name__).info("✅ Новые изображения загружены")
        return redirect(url_for('car.edit_view', id=car.id))

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
    # Remove inline models since we'll manage them in our custom view
    #inline_models = [BrandSynonym]  # This is a list with one class, not a tuple

    form_columns = ['name', 'slug', 'logo', 'country']
    column_searchable_list = ['name', 'slug']
    column_filters = ['country.name']

    can_export = True
    page_size = 30
    
    # Use our custom template for editing
    edit_template = 'admin/brand_edit.html'

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
    
    @expose('/edit/', methods=['GET', 'POST'])
    @expose('/edit/<int:id>', methods=['GET', 'POST'])
    def edit_view(self, *args, **kwargs):
        # Call the parent class's edit_view with the proper arguments
        if hasattr(super(), 'edit_view'):
            return super().edit_view(*args, **kwargs)
        return super().edit_view()
    
    @expose('/add_synonym/<int:id>', methods=['POST'])
    def add_synonym(self, id):
        """Add a synonym to a brand"""
        brand = db.session.query(Brand).get_or_404(id)
        name = request.form.get('name', '').strip()
        
        if not name:
            flash('Название синонима не может быть пустым', 'error')
            return redirect(url_for('.edit_view', id=id))
        
        # Check if this synonym already exists
        existing = db.session.query(BrandSynonym).filter_by(name=name).first()
        if existing:
            flash(f'Синоним "{name}" уже существует для бренда {existing.brand.name}', 'error')
            return redirect(url_for('.edit_view', id=id))
        
        # Create the new synonym
        synonym = BrandSynonym(name=name, brand_id=id)
        db.session.add(synonym)
        
        try:
            db.session.commit()
            flash(f'Синоним "{name}" успешно добавлен', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении синонима: {str(e)}', 'error')
        
        return redirect(url_for('.edit_view', id=id))
    
    @expose('/delete_synonym/<int:id>', methods=['POST'])
    def delete_synonym(self, id):
        """Delete a brand synonym"""
        synonym = db.session.query(BrandSynonym).get_or_404(id)
        brand_id = synonym.brand_id
        
        try:
            db.session.delete(synonym)
            db.session.commit()
            return {'success': True, 'message': 'Синоним удален'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}, 500


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


class ImageTaskAdmin(SecureModelView):
    """Admin interface for managing image generation tasks"""
    column_list = ['id', 'task_id', 'car', 'source', 'status', 'created_at', 'updated_at']
    column_searchable_list = ['task_id', 'status', 'source']
    column_filters = ['status', 'source', 'created_at']
    column_default_sort = ('created_at', True)
    can_create = False
    can_edit = False
    can_delete = True
    page_size = 20
    
    column_labels = {
        'task_id': 'ID задачи',
        'car': 'Автомобиль',
        'source': 'Источник',
        'status': 'Статус',
        'created_at': 'Создано',
        'updated_at': 'Обновлено',
        'source_image': 'Исходное изображение',
        'result_image': 'Результат',
        'prompt': 'Промпт',
        'error': 'Ошибка'
    }
    
    column_formatters = {
        'car': lambda v, c, m, p: f"{m.car.brand.name} {m.car.model} (ID: {m.car_id})" if m.car else '—',
        'created_at': lambda v, c, m, p: m.created_at.strftime('%b %d, %Y %H:%M:%S') if m.created_at else '—',
        'updated_at': lambda v, c, m, p: m.updated_at.strftime('%b %d, %Y %H:%M:%S') if m.updated_at else '—',
    }
    
    def get_query(self):
        return super().get_query().options(
            db.joinedload(ImageTask.car).joinedload(Car.brand)
        )
    
    def get_count_query(self):
        return self.session.query(db.func.count(ImageTask.id))


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
            return redirect(url_for('api_docs'), code=302)

        def is_visible(self):
            return True

    # Add Logs view link
    class LogsView(BaseView):
        @expose('/')
        def index(self):
            return redirect(url_for('view_logs'), code=302)

        def is_visible(self):
            return True

    # ===== Автомобили =====
    admin.add_view(CarAdmin(Car, db.session, name='Автомобили', category='Автомобили'))
    admin.add_view(CarImageAdmin(CarImage, db.session, name='Фотографии', category='Автомобили'))
    admin.add_view(ImageTaskAdmin(ImageTask, db.session, name='Задачи генерации', category='Автомобили'))
    
    # ===== Каталог =====
    admin.add_view(BrandAdmin(Brand, db.session, name='Марки', category='Каталог'))
    admin.add_view(CategoryAdmin(Category, db.session, name='Категории', category='Каталог'))
    admin.add_view(CarTypeAdmin(CarType, db.session, name='Типы кузова', category='Каталог'))
    
    # ===== Пользователи =====
    admin.add_view(UserAdmin(User, db.session, name='Пользователи', category='Пользователи'))
    
    class RoleAdmin(SecureModelView):
        column_list = ['name', 'description', 'user_count']
        column_searchable_list = ['name', 'description']
        column_sortable_list = ['name']  # Only allow sorting by name
        column_labels = {
            'name': 'Название',
            'description': 'Описание',
            'user_count': 'Кол-во пользователей'
        }
        form_columns = ['name', 'description']
        
        def get_query(self):
            # Get the user count for each role
            from sqlalchemy import func, or_
            from .models import user_roles
            
            # Only modify the list view query
            if not self.is_edit_view() and not self.is_create_view():
                return (db.session.query(
                    Role,
                    func.count(user_roles.c.user_id).label('user_count')
                )
                .select_from(Role)
                .outerjoin(user_roles, Role.id == user_roles.c.role_id)
                .group_by(Role.id))
            return super().get_query()
        
        def is_edit_view(self):
            from flask import request
            return request.endpoint and 'edit' in request.endpoint
            
        def is_create_view(self):
            from flask import request
            return request.endpoint and 'create' in request.endpoint
        
        def get_count_query(self):
            return self.session.query(db.func.count(Role.id))
        
        def get_pk_value(self, model):
            # Handle both SQLAlchemy Row objects and plain model instances
            if hasattr(model, '_asdict'):  # It's a Row object
                role = model[0] if len(model) > 1 else model
                return role.id
            return model.id
            
        # Format the user count for display
        def _user_count_formatter(view, context, model, name):
            # The model here is a SQLAlchemy Row object
            if hasattr(model, '_asdict'):
                return model[1] if len(model) > 1 else 0
            return 0
            
        column_formatters = {
            'user_count': _user_count_formatter,
            'name': lambda v, c, m, p: m[0].name if hasattr(m, '_asdict') and len(m) > 1 else m.name,
            'description': lambda v, c, m, p: m[0].description if hasattr(m, '_asdict') and len(m) > 1 else (m.description or '')
        }
        
        def get_one(self, id):
            # Ensure we return a plain Role instance for edit view
            return self.session.get(Role, id)
        
    admin.add_view(RoleAdmin(Role, db.session, name='Роли', category='Пользователи'))
    
    # ===== Настройки =====
    admin.add_view(CountryAdmin(Country, db.session, name='Страны', category='Настройки'))
    admin.add_view(CurrencyAdmin(Currency, db.session, name='Валюты', category='Настройки'))

    # ===== Инструменты =====
    admin.add_view(ApiDocsView(name='API Документация', category='Инструменты'))
    admin.add_view(LogsView(name='Логи', category='Инструменты'))

    return admin

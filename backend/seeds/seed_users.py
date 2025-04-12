def seed_users():
    from backend.models import db, User, Role

    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Администратор')
        db.session.add(admin_role)

    staff_role = Role.query.filter_by(name='staff').first()
    if not staff_role:
        staff_role = Role(name='staff', description='Сотрудник')
        db.session.add(staff_role)

    customer_role = Role.query.filter_by(name='customer').first()
    if not customer_role:
        customer_role = Role(name='customer', description='Покупатель')
        db.session.add(customer_role)

    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='1admin@example.com')
        admin_user.set_password('admin123')
        admin_user.roles.append(admin_role)
        db.session.add(admin_user)

    db.session.commit()
    print("✅ Пользователь и роли добавлены.")

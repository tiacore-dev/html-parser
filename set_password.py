def set_password(login, password):
    from app.database.managers.user_manager import UserManager
    db = UserManager()
    if not db.user_exists(login):
        db.add_user(login, password)
        print('New admin added successfully')

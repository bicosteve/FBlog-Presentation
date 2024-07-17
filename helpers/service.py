def validate_register_form(name, email, username, password, confirm):
    if name.strip() == "":
        return False
    if email.strip() == "":
        return False
    if username.strip() == "":
        return False

    if password.strip() == "":
        return False
    if confirm.strip() == "":
        return False
    if password != confirm:
        return False
    return True


def validate_login_form(email, password):
    if email.strip() == "":
        return False
    if password.strip() == "":
        return False
    return True


def validate_article_form(title, body):
    if title.strip() == "":
        return False
    if body.strip() == "":
        return False
    return True

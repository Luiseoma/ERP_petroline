import secrets
import string


def generar_password():
    caracteres = string.ascii_letters + string.digits

    return ''.join(
        secrets.choice(caracteres)
        for _ in range(8)
    )
from flask import session

class Models:
    @staticmethod
    def is_role(role):
        """Verifica el rol del usuario en la sesión."""
        user = session.get('user')
        return user and user.get('role') == role

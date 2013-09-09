from django.contrib.auth.models import User
from advanced_reports.backoffice.base import BackOfficeBase


class UserHelpdesk(BackOfficeBase):
    title = 'User Helpdesk'

    def __init__(self, name='userhelpdesk', app_name='userhelpdesk', **kwargs):
        super(UserHelpdesk, self).__init__(name=name, app_name=app_name, **kwargs)


class UserModel(object):
    slug = 'user'
    model = User

    def get_title(self, instance):
        return unicode(instance)

    def serialize_instance(self, instance):
        return {'first_name': instance.first_name,
                'last_name': instance.last_name}



helpdesk = UserHelpdesk()
helpdesk.register_model(UserModel)

from django.contrib.auth.models import User
from advanced_reports.backoffice.base import BackOfficeBase, BackOfficeModel


class UserHelpdesk(BackOfficeBase):
    title = 'User Helpdesk'

    def __init__(self, name='userhelpdesk', app_name='userhelpdesk', **kwargs):
        super(UserHelpdesk, self).__init__(name=name, app_name=app_name, **kwargs)


class UserModel(BackOfficeModel):
    slug = 'user'
    model = User

    def get_title(self, instance):
        return unicode(instance)

    def serialize(self, instance):
        return {'first_name': instance.first_name,
                'last_name': instance.last_name}



helpdesk = UserHelpdesk()
helpdesk.register_model(UserModel)

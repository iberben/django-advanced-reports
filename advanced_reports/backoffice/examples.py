from advanced_reports.backoffice.base import BackOfficeBase


class UserHelpdesk(BackOfficeBase):
    title = 'User Helpdesk'

    def __init__(self, name='userhelpdesk', app_name='userhelpdesk', **kwargs):
        super(UserHelpdesk, self).__init__(name=name, app_name=app_name, **kwargs)





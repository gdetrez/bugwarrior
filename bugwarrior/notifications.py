from future import standard_library
standard_library.install_aliases()

from collections import namedtuple
import datetime
from importlib import import_module
import os
import urllib.request, urllib.parse, urllib.error

from bugwarrior.config import asbool


cache_dir = os.path.expanduser(os.getenv('XDG_CACHE_HOME', "~/.cache") + "/bugwarrior")
logo_path = cache_dir + "/logo.png"
logo_url = "https://upload.wikimedia.org/wikipedia/" + \
    "en/5/59/Taskwarrior_logo.png"


def _cache_logo():
    if os.path.exists(logo_path):
        return

    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    urllib.request.urlretrieve(logo_url, logo_path)


class Notifier:

    def __init__(self, backend,
                 finished_querying_sticky=False, task_crud_sticky=False):
        self.backend = backend
        self.finished_querying_sticky = finished_querying_sticky
        self.task_crud_sticky = task_crud_sticky

    def _make_notification(self, body, sticky=False):
        return Notification(
            summary="Bugwarrior", body=body, sticky=sticky, icon=logo_path)

    def bw_finishes(self, report):
        body = "Finished querying for new issues.\n%s" % report
        self.backend.notify(
            self._make_notification(body, sticky=self.finished_querying_sticky))

    def task_change(self, op, task):
        message = "%s task: %s" % (op, task['description'])
        if 'project' in task:
            message += "\nProject: {}".format(task['project'])
        if 'priority' in task:
            message += "\nPriority: {}".format(task['priority'])
        if 'tags' in task:
            message += "\nTags: {}".format(', '.join(task['tags']))
        self.backend.notify(self._make_notification(
            message, sticky=self.task_crud_sticky))


def notification_backend(notify_backend):
    if notify_backend == 'growlnotify':
        return GrowlNotificationBackend()
    elif notify_backend == 'pynotify':
        return PynotifyNotificationBackend()
    elif notify_backend == 'gobject':
        return GobjectNotificationBackend()
    else:
        raise ValueError(
            "Unknown notification backend: {}".format(notify_backend))


def send_notification(issue, op, conf):
    notify_backend = conf.get('notifications', 'backend')
    backend = notification_backend(notify_backend)
    _cache_logo()
    notifier = Notifier(
        backend,
        finished_querying_sticky=asbool(conf.get(
            'notifications', 'finished_querying_sticky', 'True')),
        task_crud_sticky=asbool(conf.get(
            'notifications', 'task_crud_sticky', 'True')))

    if op == 'bw finished':
        notifier.bw_finished(issue['description'])
    else:
        notifier.task_change(op, issue)


Notification = namedtuple("Notification", ['summary', 'body', 'icon', 'sticky'])


class BaseNotificationBackend:
    def notify(self, notification):
        raise NotImplementedError()


class GobjectNotificationBackend(BaseNotificationBackend):
    def __init__(self):
        import_module('gi').require_version('Notify', '0.7')
        self._Notify = import_module('gi.repository.Notify')
        self._Notify.init("bugwarrior")

    def notify(self, notification):
        self._Notify.Notification.new(
            notification.summary, notification.body, notification.icon).show()


class PynotifyNotificationBackend(BaseNotificationBackend):
    def __init__(self):
        self._pynotify = import_module('pynotify')
        self._pynotify.init("bugwarrior")

    def notify(self, notification):
        self._pynotify.Notification(
            notification.summary, notification.body, notification.icon).show()


class GrowlNotificationBackend(BaseNotificationBackend):
    def __init__(self):
        self._growl = import_module('gntp.notifier').GrowlNotifier(
            applicationName="Bugwarrior",
            notifications=["New Updates", "New Messages"],
            defaultNotifications=["New Messages"],
        )
        self._growl.register()

    def notify(self, notification):
        self._growl.notify(
            noteType="New Messages",
            title=notification.summary,
            description=notification.body,
            sticky=notification.sticky,
            icon="file://" + notification.icon,
            priority=1,
            )

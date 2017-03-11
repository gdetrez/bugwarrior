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


def _get_metadata(issue):
    due = ''
    tags = ''
    priority = ''
    metadata = ''
    project = ''
    if 'project' in issue:
        project = "Project: " + issue['project']
    # if 'due' in issue:
    #     due = "Due: " + datetime.datetime.fromtimestamp(
    #         int(issue['due'])).strftime('%Y-%m-%d')
    if 'tags' in issue:
        tags = "Tags: " + ', '.join(issue['tags'])
    if 'priority' in issue:
        priority = "Priority: " + issue['priority']
    if project != '':
        metadata += "\n" + project
    if priority != '':
        metadata += "\n" + priority
    if due != '':
        metadata += "\n" + due
    if tags != '':
        metadata += "\n" + tags
    return metadata


def send_notification(issue, op, conf):
    notify_backend = conf.get('notifications', 'backend')

    # Notifications for growlnotify on Mac OS X
    if notify_backend == 'growlnotify':
        backend = GrowlNotificationBackend()
    elif notify_backend == 'pynotify':
        backend = PynotifyNotificationBackend()
    elif notify_backend == 'gobject':
        backend = GobjectNotificationBackend()
    else:
        raise ValueError(
            "Unknown notification backend: {}".format(notify_backend))

    _cache_logo()

    if op == 'bw finished':
        notification = Notification(
            summary="Bugwarrior",
            body="Finished querying for new issues.\n%s" % issue['description'],
            icon=logo_path,
            sticky=asbool(conf.get(
                    'notifications', 'finished_querying_sticky', 'True')))
    else:
        message = "%s task: %s" % (op, issue['description'])
        metadata = _get_metadata(issue)
        if metadata is not None:
            message += metadata
        notification = Notification(
            summary="Bugwarrior",
            body=message,
            icon=logo_path,
            sticky=asbool(conf.get(
                    'notifications', 'task_crud_sticky', 'True')))

    backend.notify(notification)


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

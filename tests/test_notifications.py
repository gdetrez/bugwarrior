# coding: utf-8
import unittest
from collections import OrderedDict
from mock import MagicMock

from bugwarrior.notifications import Notification, Notifier, logo_path


class TestNotifier(unittest.TestCase):

    def setUp(self):
        self.backend = MagicMock()

    def assertNotificationSent(self, notification):
        self.backend.notify.assert_called_with(notification)

    def test_make_notification(self):
        notifier = Notifier(self.backend)
        expected = Notification(
            summary=u"Bugwarrior", body=u"Take me to your leader",
            icon=logo_path, sticky=False)
        actual = notifier._make_notification(u"Take me to your leader")
        self.assertEquals(expected, actual)

    def test_make_notification_sticky(self):
        notifier = Notifier(self.backend)
        expected = Notification(
            summary=u"Bugwarrior", body=u"Take me to your leader",
            icon=logo_path, sticky=True)
        actual = notifier._make_notification(u"Take me to your leader", sticky=True)
        self.assertEquals(expected, actual)

    def test_make_notification_with_summary(self):
        notifier = Notifier(self.backend)
        expected = Notification(
            summary=u"Bugwarrior: Bzzzzz", body=u"Take me to your leader",
            icon=logo_path, sticky=False)
        actual = notifier._make_notification(
            u"Take me to your leader", summary=u"Bzzzzz")
        self.assertEquals(expected, actual)

    def test_on_pull_finished(self):
        notifier = Notifier(self.backend)
        notifier.on_pull_finished(
            None, stats=OrderedDict([('new', 3), ('changed', 1), ('completed', 2)]))
        self.assertNotificationSent(Notification(
            summary=u"Bugwarrior: Finished querying for new issues.",
            body=u"New: 3, Changed: 1, Completed: 2",
            icon=logo_path, sticky=False))

    def test_on_pull_finished_sticky(self):
        notifier = Notifier(self.backend, finished_querying_sticky=True)
        notifier.on_pull_finished(
            None, stats=OrderedDict([('new', 3), ('changed', 1), ('completed', 2)]))
        self.assertNotificationSent(Notification(
            summary=u"Bugwarrior: Finished querying for new issues.",
            body=u"New: 3, Changed: 1, Completed: 2",
            icon=logo_path, sticky=True))

    def test_on_task_created(self):
        notifier = Notifier(self.backend)
        notifier.on_task_created(
            None, task={'description': u"(bw)#42: Bring your towel"})
        self.assertNotificationSent(Notification(
            summary=u"Bugwarrior: New task",
            body=u"(bw)#42: Bring your towel",
            icon=logo_path, sticky=False))

    def test_on_task_created_sticky(self):
        notifier = Notifier(self.backend, task_crud_sticky=True)
        notifier.on_task_created(
            None, task={'description': u"(bw)#42: Bring your towel"})
        self.assertNotificationSent(Notification(
            summary=u"Bugwarrior: New task",
            body=u"(bw)#42: Bring your towel",
            icon=logo_path, sticky=True))

    def test_on_task_created_project(self):
        notifier = Notifier(self.backend)
        task = {
            'description': u"(bw)#42: Bring your towel",
            'project': u"dont-panic",
        }
        notifier.on_task_created('Create', task=task)
        self.assertNotificationSent(Notification(
            summary=u"Bugwarrior: New task in project dont-panic",
            body=u"(bw)#42: Bring your towel",
            icon=logo_path, sticky=False))

    def test_on_task_created_metadata(self):
        notifier = Notifier(self.backend)
        task = {
            'description': u"(bw)#42: Bring your towel",
            'tags': [u"life", u"the universe", u"everything"],
            'priority': 'H',
        }
        notifier.on_task_created('Create', task=task)
        self.assertNotificationSent(Notification(
            summary=u"Bugwarrior: New task",
            body=u"(bw)#42: Bring your towel\n"
                 u"Priority: H\n"
                 u"Tags: life, the universe, everything",
            icon=logo_path, sticky=False))

    def test_on_task_updated(self):
        notifier = Notifier(self.backend)
        notifier.on_task_updated(
            None, task={'description': u"(bw)#42: Bring your towel"})
        self.assertNotificationSent(Notification(
            summary=u"Bugwarrior: Task updated",
            body=u"(bw)#42: Bring your towel",
            icon=logo_path, sticky=False))

    def test_on_task_completed(self):
        notifier = Notifier(self.backend)
        notifier.on_task_completed(
            None, task={'id': 10, 'description': u"(bw)#42: Bring your towel"})
        self.assertNotificationSent(Notification(
            summary=u"Bugwarrior: Task 10 done",
            body=u"(bw)#42: Bring your towel",
            sticky=False, icon=logo_path))


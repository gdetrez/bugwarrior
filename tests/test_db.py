from mock import Mock, patch
import unittest

import taskw.task
from bugwarrior.db import (
    merge_left, create_task, _notreally, modify_task, close_task)


class DBTest(unittest.TestCase):
    def setUp(self):
        self.issue_dict = {'annotations': ['testing']}

    def test_merge_left_with_dict(self):
        task = {}
        merge_left('annotations', task, self.issue_dict)
        self.assertEquals(task, self.issue_dict)

    def test_merge_left_with_taskw(self):
        task = taskw.task.Task({})
        merge_left('annotations', task, self.issue_dict)
        self.assertEquals(task, self.issue_dict)


class CreateTaskTest(unittest.TestCase):

    def setUp(self):
        self.tw = Mock()
        self.issue = { 'description': 'foobar', 'myattr': 42 }

    def test_create_task(self):
        create_task(self.tw, self.issue, False, False, False, None)
        self.tw.task_add.assert_called_once_with(**self.issue)

    def test_create_task_dry_run(self):
        create_task(self.tw, self.issue, True, False, False, None)
        self.tw.task_add.assert_not_called()

    @patch('bugwarrior.db.send_notification')
    def test_close_task_notify(self, send_notification_mock):
        create_task(self.tw, self.issue, False, False, True, None)
        send_notification_mock.assert_called()

    @patch('bugwarrior.db.input', return_value='a')
    def test_create_task_timid_apply(self, input_mock):
        create_task(self.tw, self.issue, False, True, False, None)
        self.tw.task_add.assert_called_once_with(**self.issue)

    @patch('bugwarrior.db.input', return_value='s')
    def test_create_task_timid_skip(self, input_mock):
        create_task(self.tw, self.issue, False, True, False, None)
        self.tw.task_add.assert_not_called()


class ModifyTaskTest(unittest.TestCase):

    def setUp(self):
        self.tw = Mock()
        self.task = taskw.task.Task(
            {'uuid': '12345678123456781234567812345678', 'description': "foobar", 'myattr': 42})
        self.task.update({'myattr': 43})

    def test_modify_task(self):
        modify_task(self.tw, self.task, False, False)
        self.tw.task_update.assert_called_once_with(self.task)

    def test_dry_run(self):
        modify_task(self.tw, self.task, True, False)
        self.tw.task_update.assert_not_called()

    @patch('bugwarrior.db.input', return_value='a')
    def test_create_task_timid_apply(self, input_mock):
        modify_task(self.tw, self.task, False, True)
        self.tw.task_update.assert_called_once_with(self.task)

    @patch('bugwarrior.db.input', return_value='s')
    def test_create_task_timid_skip(self, input_mock):
        modify_task(self.tw, self.task, False, True)
        self.tw.task_update.assert_not_called()


class CloseTaskTest(unittest.TestCase):

    def setUp(self):
        task = taskw.task.Task(
            {'uuid': '12345678123456781234567812345678',
             'description': "foobar",
             'myattr': 42})
        self.tw = Mock()
        self.tw.get_task.return_value = (None, task)
        self.uuid = task['uuid']
        self.conf = Mock()

    def test_close_task(self):
        close_task(self.tw, self.uuid, False, False, False, None)
        self.tw.task_done.assert_called_once_with(uuid=self.uuid)

    def test_close_task_dry_run(self):
        close_task(self.tw, self.uuid, True, False, False, None)
        self.tw.task_done.assert_not_called()

    @patch('bugwarrior.db.send_notification')
    def test_close_task_notify(self, send_notification_mock):
        close_task(self.tw, self.uuid, False, False, True, None)
        send_notification_mock.assert_called()

    @patch('bugwarrior.db.input', return_value='a')
    def test_close_task_timid_apply(self, input_mock):
        close_task(self.tw, self.uuid, False, False, False, None)
        self.tw.task_done.assert_called_once_with(uuid=self.uuid)

    @patch('bugwarrior.db.input', return_value='s')
    def test_close_task_timid_skip(self, input_mock):
        close_task(self.tw, self.uuid, False, True, False, None)
        self.tw.task_done.assert_not_called()

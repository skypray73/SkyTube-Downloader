"""Exercise batch lifecycle without opening a window or accessing YouTube."""
import queue
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app import App


class BatchTests(unittest.TestCase):
    def runner(self, results):
        return SimpleNamespace(events=queue.Queue(), stop_event=threading.Event(),
                               run_one=Mock(side_effect=results))

    def events(self, runner):
        return list(runner.events.queue)

    def test_partial_playlist_failure_continues_next_link(self):
        runner = self.runner([(1, 2), (0, 1)])
        App.run(runner, [['--', 'playlist'], ['--', 'video']])
        self.assertEqual(runner.run_one.call_count, 2)
        self.assertEqual(self.events(runner)[-1], ('done', dict(
            total=2, completed=1, failed=1, files=3)))
        self.assertEqual([value for kind, value in self.events(runner) if kind == 'link'],
                         [(1, 2), (2, 2)])

    def test_cancel_does_not_start_remaining_links(self):
        runner = self.runner([])
        def cancel(args):
            runner.stop_event.set()
            return 1, 1
        runner.run_one.side_effect = cancel
        App.run(runner, [['one'], ['two']])
        self.assertEqual(runner.run_one.call_count, 1)
        self.assertEqual(self.events(runner)[-1][1], dict(
            total=2, completed=0, failed=0, files=1))

    def test_cancel_before_worker_starts(self):
        runner = self.runner([])
        runner.stop_event.set()
        App.run(runner, [['one']])
        runner.run_one.assert_not_called()
        self.assertEqual(self.events(runner)[-1][0], 'done')

    def test_all_success(self):
        runner = self.runner([(0, 1), (0, 3)])
        App.run(runner, [['one'], ['two']])
        self.assertEqual(self.events(runner)[-1][1], dict(
            total=2, completed=2, failed=0, files=4))


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import sys

# Add the script to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import auto_scheduler

class TestAutoSchedulerGitSync(unittest.TestCase):

    @patch('auto_scheduler.subprocess.run')
    def test_pull_git_updates(self, mock_run):
        # Setup mock behavior
        mock_result = MagicMock()
        mock_result.stdout = "Updating 1da02a3..208d232\nFast-forward\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        queue_path = "/fake/workspace/experiment_queue.json"
        
        # Execute the function
        auto_scheduler.pull_git_updates(queue_path)
        
        # Verify it executed exactly the right command format
        expected_cmd = "cd /fake/workspace && GIT_SSH_COMMAND=\"ssh -o Port=443 -o HostName=ssh.github.com -o ConnectTimeout=15 -o StrictHostKeyChecking=no\" git pull origin main"
        mock_run.assert_called_with(expected_cmd, shell=True, capture_output=True, text=True, timeout=30)
        
    @patch('auto_scheduler.subprocess.run')
    def test_sync_queue_to_git(self, mock_run):
        # Setup mock behavior
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        queue_path = "/fake/workspace/experiment_queue.json"
        
        # Execute the function
        auto_scheduler.sync_queue_to_git(queue_path)
        
        # Verify it executed the git status check and push
        expected_cmd = "cd /fake/workspace && git add experiment_queue.json && git commit -m 'chore: Auto-Scheduler state pulse checkpoint' && GIT_SSH_COMMAND=\"ssh -o Port=443 -o HostName=ssh.github.com -o ConnectTimeout=15 -o StrictHostKeyChecking=no\" git push origin main"
        mock_run.assert_called_with(expected_cmd, shell=True, capture_output=True, timeout=30)
        
    @patch('auto_scheduler.get_file_lock')
    @patch('auto_scheduler.release_file_lock')
    @patch('auto_scheduler.pull_git_updates')
    @patch('auto_scheduler.sync_queue_to_git')
    def test_daemon_loop_sync_trigger(self, mock_push, mock_pull, mock_release, mock_get_lock):
        """Test if the daemon loop correctly triggers bidirectional sync."""
        # A lightweight test to ensure that when git_sync_needed triggers, push is called
        # Mocking the queue pruning to return True for pruned_flag
        with patch('auto_scheduler.prune_queue_locked', return_value=({"tasks": []}, True)):
            with patch('auto_scheduler.time.sleep', side_effect=InterruptedError("Stop loop")):
                args = MagicMock()
                args.mode = "local"
                args.queue = "/fake/q.json"
                args.poll = 5
                
                try:
                    auto_scheduler.daemon_loop(args)
                except InterruptedError:
                    pass
                
                # Check that pull was called at the start of loop
                mock_pull.assert_called_with(args.queue)
                
                # Check that push was called because pruned_flag = True (simulating git sync needed)
                mock_push.assert_called_with(args.queue)

if __name__ == '__main__':
    unittest.main()

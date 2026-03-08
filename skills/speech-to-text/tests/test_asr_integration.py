#!/usr/bin/env python3
"""
ASR Integration and Unit Tests (PDCA Automated Validation)
"""

import os
import sys
import subprocess
import pytest
from unittest.mock import patch, MagicMock

# Dynamically add the target script directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.abspath(os.path.join(current_dir, "..", "scripts"))
sys.path.insert(0, scripts_dir)

import asr_tool


class TestASRTool:
    
    @patch("asr_tool.run_cmd")
    @patch("os.path.exists")
    @patch("sys.exit")
    def test_parameter_assembly_mock(self, mock_exit, mock_exists, mock_run_cmd):
        """
        1. [Unit Mock Barrier] 断言参数拼装的精确度
        测试不发送真实 SSH，拦截底层 run_cmd 的所有调用。
        断言命令字符串是否 100% 符合预期（防幻觉断言）。
        """
        # Fake that everything exists (audio file and ssh_tool.py)
        mock_exists.return_value = True
        
        # Override sys.argv to simulate user input
        test_args = ["asr_tool.py", "/tmp/fake_audio.wav", "--model", "large-v3-turbo-q5_0", "--language", "zh"]
        with patch.object(sys, 'argv', test_args):
            # Capture print statements to avoid console noise
            with patch("builtins.print"):
                asr_tool.main()
                
        # main() makes 3 calls to run_cmd (upload, exec asr, exec rm)
        assert mock_run_cmd.call_count == 3, "应该正好有 3 步远端调用！"
        
        # Assert Upload Command
        upload_call_cmd = mock_run_cmd.call_args_list[0][0][0]
        assert "upload /tmp/fake_audio.wav /tmp/fake_audio.wav" in upload_call_cmd
        
        # Assert Main Inference Command
        exec_call_cmd = mock_run_cmd.call_args_list[1][0][0]
        assert "exec" in exec_call_cmd
        assert "~/.openclaw_deps/whisper.cpp/main" in exec_call_cmd
        assert "-m ~/.openclaw_deps/whisper.cpp/models/ggml-large-v3-turbo-q5_0.bin" in exec_call_cmd
        assert "-f /tmp/fake_audio.wav" in exec_call_cmd
        assert "-l zh -nt" in exec_call_cmd

    def test_fail_fast_on_missing_audio(self):
        """
        2. [Fail-Fast Verification] 边界防波堤
        输入不存在的录音文件，断言能被前置防线猎杀，抛出合规的 Exit(1)。
        """
        test_args = ["asr_tool.py", "/tmp/ghost_audio_that_does_not_exist.wav"]
        with patch.object(sys, 'argv', test_args):
            with patch("builtins.print") as mock_print:
                with pytest.raises(SystemExit) as excinfo:
                    asr_tool.main()
                
        # Ensure sys.exit(1) was called gracefully
        assert excinfo.value.code == 1
        
        # Ensure the failure reason was broadcasted to stdout
        printed_msg = mock_print.call_args_list[0][0][0]
        assert "❌ 找不到本地音频文件" in printed_msg

    @pytest.mark.skipif(os.environ.get("RUN_LIVE_TESTS") != "true", reason="需要环境变量 RUN_LIVE_TESTS=true 才能轰击实机")
    def test_live_fire_end_to_end(self):
        """
        3. [Live Fire End-to-End Test] 实弹穿透打靶
        伪造真人生效，远端真实传唤 M1 推理。
        """
        audio_path = "/tmp/real_test_live_fire.wav"
        
        # 1. 制造“弹药”：用内置 say 生成高质量 .wav
        subprocess.run(f"say -o {audio_path} --data-format=LEI16@16000 '兵器就绪长官，反幻觉守卫系统已上线'", shell=True, check=True)
        assert os.path.exists(audio_path), "本地测试弹药生成失败！"
        
        # 2. 调用兵器主程序进行实弹打击
        test_args = ["asr_tool.py", audio_path, "--language", "zh"]
        try:
            with patch.object(sys, 'argv', test_args):
                with patch("builtins.print") as mock_print:
                    asr_tool.main()
                    
            # 3. 猎取战果
            # main() prints the result at the very end
            result_str = None
            for call in mock_print.call_args_list:
                msg = call[0][0]
                if isinstance(msg, str) and "兵器" in msg:
                    result_str = msg
                    break
                    
            assert result_str is not None, "远端未回传包含有效关键词的识别结果！"
            assert "兵器" in result_str or "长官" in result_str, f"实装识别似乎错乱！实际回传：{result_str}"
            
        finally:
            # 清扫战场
            if os.path.exists(audio_path):
                os.remove(audio_path)

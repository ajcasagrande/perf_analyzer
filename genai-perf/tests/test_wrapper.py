# Copyright 2024-2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of NVIDIA CORPORATION nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pytest
from genai_perf import parser
from genai_perf.constants import DEFAULT_GRPC_URL
from genai_perf.wrapper import Profiler


class TestWrapper:
    @pytest.mark.parametrize(
        "arg",
        [
            ([]),
            (["-u", "testurl:1000"]),
            (["--url", "testurl:1000"]),
        ],
    )
    def test_url_exactly_once_triton(self, monkeypatch, arg):
        args = [
            "genai-perf",
            "profile",
            "-m",
            "test_model",
            "--service-kind",
            "triton",
        ] + arg
        monkeypatch.setattr("sys.argv", args)
        args, extra_args = parser.parse_args()
        cmd = Profiler.build_cmd(args, extra_args)
        cmd_string = " ".join(cmd)

        number_of_url_args = cmd_string.count(" -u ") + cmd_string.count(" --url ")
        assert number_of_url_args == 1

    @pytest.mark.parametrize(
        "arg, expected_filepath",
        [
            (
                [],
                "artifacts/test_model-triton-tensorrtllm-concurrency1/profile_export.json",
            ),
            (
                ["--artifact-dir", "test_dir"],
                "test_dir/profile_export.json",
            ),
            (
                ["--artifact-dir", "test_dir", "--profile-export-file", "test.json"],
                "test_dir/test.json",
            ),
        ],
    )
    def test_profile_export_filepath(self, monkeypatch, arg, expected_filepath):
        args = [
            "genai-perf",
            "profile",
            "-m",
            "test_model",
            "--service-kind",
            "triton",
        ] + arg
        monkeypatch.setattr("sys.argv", args)
        args, extra_args = parser.parse_args()
        cmd = Profiler.build_cmd(args, extra_args)
        cmd_string = " ".join(cmd)

        expected_pattern = f"--profile-export-file {expected_filepath}"
        assert expected_pattern in cmd_string

    @pytest.mark.parametrize(
        "arg",
        [
            (["--backend", "tensorrtllm"]),
            (["--backend", "vllm"]),
        ],
    )
    def test_service_triton(self, monkeypatch, arg):
        args = [
            "genai-perf",
            "profile",
            "-m",
            "test_model",
            "--service-kind",
            "triton",
        ] + arg
        monkeypatch.setattr("sys.argv", args)
        args, extra_args = parser.parse_args()
        cmd = Profiler.build_cmd(args, extra_args)
        cmd_string = " ".join(cmd)

        # Ensure the correct arguments are appended.
        assert cmd_string.count(" -i grpc") == 1
        assert cmd_string.count(" --streaming") == 1
        assert cmd_string.count(f"-u {DEFAULT_GRPC_URL}") == 1
        if arg[1] == "tensorrtllm":
            assert cmd_string.count("--shape max_tokens:1") == 1
            assert cmd_string.count("--shape text_input:1") == 1

    @pytest.mark.parametrize(
        "arg",
        [
            (["--endpoint-type", "completions"]),
            (["--endpoint-type", "chat"]),
        ],
    )
    def test_service_openai(self, monkeypatch, arg):
        args = [
            "genai-perf",
            "profile",
            "-m",
            "test_model",
            "--service-kind",
            "openai",
        ] + arg
        monkeypatch.setattr("sys.argv", args)
        args, extra_args = parser.parse_args()
        cmd = Profiler.build_cmd(args, extra_args)
        cmd_string = " ".join(cmd)

        # Ensure the correct arguments are appended.
        assert cmd_string.count(" -i http") == 1

    @pytest.mark.parametrize(
        "header_values, expected_headers",
        [
            (["Header1:Value1"], [("-H", "Header1:Value1")]),
            (
                ["Authorization:Bearer mytoken", "Content-Type:application/json"],
                [
                    ("-H", "Authorization:Bearer mytoken"),
                    ("-H", "Content-Type:application/json"),
                ],
            ),
        ],
    )
    def test_headers_passed_correctly(
        self, monkeypatch, header_values, expected_headers
    ):
        args = [
            "genai-perf",
            "profile",
            "-m",
            "test_model",
        ]
        for header in header_values:
            args += ["-H", header]
        monkeypatch.setattr("sys.argv", args)

        args, extra_args = parser.parse_args()
        cmd = Profiler.build_cmd(args, extra_args)

        for expected_flag, expected_value in expected_headers:
            try:
                flag_index = cmd.index(expected_flag)
                assert cmd[flag_index + 1] == expected_value, (
                    f"Header value mismatch for {expected_flag}: "
                    f"Expected {expected_value}, Found {cmd[flag_index + 1]}"
                )
                cmd[flag_index] = None  # type: ignore
                cmd[flag_index + 1] = None  # type: ignore
            except ValueError:
                assert (
                    False
                ), f"Missing expected header flag: {expected_flag} or value: {expected_value}"

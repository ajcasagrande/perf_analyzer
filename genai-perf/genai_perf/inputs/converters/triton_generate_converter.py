# Copyright 2024, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from typing import Any, Dict

from genai_perf.inputs.converters.base_converter import BaseConverter
from genai_perf.inputs.input_constants import DEFAULT_OUTPUT_TOKENS_MEAN
from genai_perf.inputs.inputs_config import InputsConfig
from genai_perf.inputs.retrievers.generic_dataset import GenericDataset
from genai_perf.utils import sample_bounded_normal


class TritonGenerateConverter(BaseConverter):

    def check_config(self, config: InputsConfig) -> None:
        if config.output_tokens_deterministic:
            raise ValueError(
                "The --output-tokens-deterministic flag is not supported for Triton Generate."
            )

    def convert(
        self,
        generic_dataset: GenericDataset,
        config: InputsConfig,
    ) -> Dict[Any, Any]:
        request_body: Dict[str, Any] = {"data": []}

        for file_data in generic_dataset.files_data.values():
            for _, row in enumerate(file_data.rows):
                prompt = row.texts

                payload = {
                    "text_input": prompt,
                }
                self._add_request_params(payload, config)
                request_body["data"].append({"payload": [payload]})

        return request_body

    def _add_request_params(self, payload: Dict, config: InputsConfig) -> None:
        if config.add_stream:
            payload["stream"] = True
        if config.output_tokens_mean != DEFAULT_OUTPUT_TOKENS_MEAN:
            payload["max_tokens"] = int(
                sample_bounded_normal(
                    mean=config.output_tokens_mean,
                    stddev=config.output_tokens_stddev,
                    lower=1,  # output token must be >= 1
                )
            )
        for key, value in config.extra_inputs.items():
            payload[key] = value

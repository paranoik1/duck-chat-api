from enum import Enum


class ModelType(Enum):
    Gpt4OMini = "gpt-4o-mini"
    Gpt5Mini = "gpt-5-mini"
    GptOss120B = "openai/gpt-oss-120b"
    Llama4Scout17B16EInstruct = "meta-llama/Llama-4-Scout-17B-16E-Instruct"
    Claude35HaikuLatest = "claude-3-5-haiku-latest"
    MistralSmall24BInstruct2501 = "mistralai/Mistral-Small-24B-Instruct-2501"
    DEFAULT = Gpt4OMini

"""Utility & helper functions."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage


def get_message_text(msg: BaseMessage) -> str:
    """
    Extracts the text content of a BaseMessage, handling various formats.

    The content of a BaseMessage can be a string, a dictionary with a "text" key,
    or a list of strings and/or dictionaries. This function will extract the text
    content from any of these formats.

    Args:
        msg: The BaseMessage to extract the text from

    Returns:
        The extracted text content
    """

    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def load_chat_model(fully_specified_name: str) -> BaseChatModel:
    """
    Loads a chat model based on the specified fully qualified name.

    The function expects a string that specifies the provider and model name
    in the format 'provider/model'. It splits this string to extract the provider
    and model name, then initializes the chat model using these details.

    Args:
        fully_specified_name: A string in the format 'provider/model', indicating
                              the provider and model to be loaded.

    Returns:
        An instance of BaseChatModel initialized with the specified model and provider.
    """

    provider, model = fully_specified_name.split("/", maxsplit=1)
    return init_chat_model(model, model_provider=provider)

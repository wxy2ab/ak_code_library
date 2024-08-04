import json
import openai
import base64
from typing import Union, List, Dict, Any, Iterator
from ._llm_api_client import LLMApiClient
from ..utils.config_setting import Config
from ..utils.handle_max_tokens import handle_max_tokens

class OpenAIClient(LLMApiClient):

    def __init__(self,
                 api_key: str = "",
                 model="gpt-4o",
                 base_url: str = "",
                 max_tokens: int = 4000,
                 temperature: float = 0.3,
                 top_p: float = 1,
                 presence_penalty: float = 0,
                 frequency_penalty: float = 0,
                 stop: Union[str, List[str]] = None):
        config = Config()
        if api_key == "" and config.has_key("OPENAI_API_KEY"):
            api_key = config.get("OPENAI_API_KEY")
        self.api_key = api_key
        if base_url:
            self.base_url = base_url
            self.client = openai.OpenAI(api_key=self.api_key,
                                        base_url=self.base_url)
        else:
            self.client = openai.OpenAI(api_key=self.api_key)
        self.chat_count = 0
        self.token_count = 0
        self.history = []
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.stop = stop

    def set_system_message(self,
                           system_message: str = "你是个智能助手，你遵循指令和写代码的能力超级棒."):
        self.history = [{"role": "system", "content": system_message}]
    @handle_max_tokens
    def text_chat(self,
                  message: str,
                  is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        self.history.append({"role": "user", "content": message})
        return self._create_chat_completion(self.history, is_stream)

    def one_chat(self,
                 message: str,
                 is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        msg = [{
            "role": "user",
            "content": message
        }] if isinstance(message, str) else message
        return self._create_chat_completion(msg, is_stream)

    def tool_chat(self,
                  user_message: str,
                  tools: List[Dict[str, Any]],
                  function_module: Any,
                  is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()
        self.history.append({"role": "user", "content": user_message})
        if is_stream:
            return self._unified_tool_stream(self.history, tools,
                                             function_module)
        else:
            response = self._create_chat_completion(self.history, is_stream,
                                                    tools)
            return self._process_tool_response(response, tools,
                                               function_module)

    def image_chat(self,
                   message: str,
                   image_path_or_url: str,
                   is_stream: bool = False) -> Union[str, Iterator[str]]:
        if not self.history:
            self.set_system_message()

        if image_path_or_url.startswith(
                "http://") or image_path_or_url.startswith("https://"):
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": image_path_or_url
                }
            }
        else:
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": self._encode_image_to_base64(image_path_or_url)
                }
            }

        self.history.append({
            "role":
            "user",
            "content": [{
                "type": "text",
                "text": message
            }, image_content]
        })
        return self._create_chat_completion(self.history, is_stream)

    def _encode_image_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_image}"

    def _unified_tool_stream(self, messages: List[Dict[str, str]],
                             tools: List[Dict[str, Any]],
                             function_module: Any) -> Iterator[str]:
        try:
            response_stream = self._create_chat_completion(messages,
                                                           True,
                                                           tools,
                                                           raw_response=True)
            full_response = ""
            tool_calls = []

            for chunk in response_stream:
                if isinstance(chunk, str):
                    content = chunk
                elif hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    content = delta.content if hasattr(
                        delta,
                        'content') and delta.content is not None else None
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            if tool_call.index >= len(tool_calls):
                                tool_calls.append({
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name":
                                        tool_call.function.name,
                                        "arguments":
                                        tool_call.function.arguments or ""
                                    }
                                })
                            else:
                                tool_calls[tool_call.index]["function"][
                                    "arguments"] += tool_call.function.arguments or ""
                if content:
                    yield content
                    full_response += content

            if tool_calls:
                tool_outputs = self._execute_tool_calls(
                    tool_calls, function_module)
                tool_results = []
                for tool_output in tool_outputs:
                    result = f"Tool {tool_output['tool_call_id']} returned result: {tool_output['content']}"
                    tool_results.append(result)
                    yield result + "\n"

                tool_result_message = "\n".join(tool_results)
                messages.append({
                    "role":
                    "assistant",
                    "content":
                    f"{full_response}\n\nTool call results:\n{tool_result_message}"
                })

                explanation_request = "Please explain the above tool call results and provide a concise answer."
                messages.append({
                    "role": "user",
                    "content": explanation_request
                })

                explanation_stream = self._create_chat_completion(
                    messages, True, tools, raw_response=True)
                for chunk in explanation_stream:
                    if isinstance(chunk, str):
                        yield chunk
                    elif hasattr(chunk, 'choices') and chunk.choices:
                        delta = chunk.choices[0].delta
                        content = delta.content if hasattr(
                            delta,
                            'content') and delta.content is not None else None
                        if content:
                            yield content
            elif full_response.strip():
                yield f"\n{full_response}\n"
            else:
                yield "\nUnable to generate a response. Please try again.\n"
        except Exception as e:
            yield f"An error occurred: {str(e)}"

        self.history = [
            msg for msg in messages[-5:] if msg.get('content', '').strip()
        ]

    def _create_chat_completion(
            self,
            messages: List[Dict[str, str]],
            is_stream: bool,
            tools: List[Dict[str, Any]] = None,
            raw_response: bool = False) -> Union[str, Iterator[str]]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "stop": self.stop,
            "stream": is_stream
        }
        if tools:
            kwargs["tools"] = tools

        completion = self.client.chat.completions.create(**kwargs)
        if is_stream:
            return completion if raw_response else self._process_stream(
                completion)
        else:
            response = completion.choices[0].message.content
            self._update_stats(completion.usage)
            return response

    def _process_tool_response(self, response, tools: List[Dict[str, Any]],
                               function_module: Any) -> str:
        assistant_output = response.choices[0].message
        self._update_stats(response.usage)

        if hasattr(assistant_output,
                   'tool_calls') and assistant_output.tool_calls:
            self.history.append({
                "role": "assistant",
                "content": assistant_output.content,
                "tool_calls": assistant_output.tool_calls
            })
            tool_outputs = self._execute_tool_calls(
                assistant_output.tool_calls, function_module)
            self.history.extend(tool_outputs)
            second_response = self._create_chat_completion(
                self.history, False, tools)
            final_output = second_response.choices[0].message.content
        else:
            self.history.append({
                "role": "assistant",
                "content": assistant_output.content
            })
            final_output = assistant_output.content

        return final_output

    def _process_stream(self, stream) -> Iterator[str]:
        full_response = ""
        for chunk in stream:
            if hasattr(chunk, 'choices') and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    full_response += delta.content
                    yield delta.content
        self.history.append({"role": "assistant", "content": full_response})

    def _execute_tool_calls(self, tool_calls,
                            function_module: Any) -> List[Dict[str, str]]:
        tool_outputs = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            if hasattr(function_module, tool_name):
                tool_func = getattr(function_module, tool_name)
                try:
                    tool_output = tool_func(**tool_args)
                    tool_outputs.append({
                        "name": tool_name,
                        "content": str(tool_output),
                        "tool_call_id": tool_call.id
                    })
                except Exception as e:
                    tool_outputs.append({
                        "name": tool_name,
                        "content": f"Error executing {tool_name}: {str(e)}",
                        "tool_call_id": tool_call.id
                    })
            else:
                tool_outputs.append({
                    "name": tool_name,
                    "content": f"Error: Function {tool_name} not found.",
                    "tool_call_id": tool_call.id
                })

        return tool_outputs

    def _update_stats(self, usage: Dict):
        self.chat_count += 1

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_chats": self.chat_count,
            "total_tokens": self.token_count
        }

    def clear_chat(self) -> None:
        self.history = []

    def audio_chat(self, message: str, audio_path: str) -> str:
        raise NotImplementedError("OpenAI API does not support audio chat.")

    def video_chat(self, message: str, video_path: str) -> str:
        raise NotImplementedError("OpenAI API does not support video chat.")

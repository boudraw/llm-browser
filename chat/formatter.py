from chat.message import ResponseFormat
from chat.tool import Tool, FunctionCall, get_context
from typing import List
import json
import xml.etree.ElementTree as ET


def parse_function_calls(xml):
    function_calls = []
    try:
        root = ET.fromstring(f"<function_calls>{xml.split('<function_calls>')[1].split('</function_calls>')[0]}</function_calls>")
    except IndexError or ET.ParseError:
        return function_calls
    for invoke_element in root.findall('invoke'):
        function_call = FunctionCall(ET.tostring(invoke_element, encoding='unicode'))
        function_calls.append(function_call)
    return function_calls


class MessageFormatter:
    def __init__(self, tools: List[Tool] = None):
        self.tools = tools

    def format_output(self, output, output_format: ResponseFormat):
        if output_format == ResponseFormat.JSON:
            if type(output) == dict:
                return output
            if "```json" not in output:
                return json.loads(output.replace("\n", ""))
            return json.loads(output.split("```json")[1].split("```")[0].replace("\n", ""))
        if output_format == ResponseFormat.PYTHON:
            return output.split("```python")[1].split("```")[0]
        elif output_format == ResponseFormat.TEXT:
            return output
        elif output_format == ResponseFormat.FUNCTION_CALLS:
            function_calls = parse_function_calls(output)
            try:
                output = output.split('<scratchpad>')[1].split('</scratchpad>')[0].strip()
            except IndexError:
                try:
                    output = output.split('<result>')[1].split('</result>')[0].strip()
                except IndexError:
                    try:
                        output = output.split('<function_results>')[0].strip()
                    except IndexError:
                        output = output

                pass
            return output, function_calls
        else:
            raise ValueError("Invalid Output Format")

    def system_context(self, output_format: ResponseFormat):
        if output_format == ResponseFormat.JSON:
            return "Reply with JSON objects ONLY. Encase the JSON using ```json in the beginning, and ``` at the end."
        if output_format == ResponseFormat.PYTHON:
            return "Only reply with Python code. The code should always begin with ```python and have ``` at the end."
        elif output_format == ResponseFormat.TEXT:
            return ""
        elif output_format == ResponseFormat.FUNCTION_CALLS:
            return get_context(self.tools)
        else:
            raise ValueError("Invalid Output Format")
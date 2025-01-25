from typing import List
import xml.etree.ElementTree as ET


# <tool_description>
# <tool_name>get_ticker_symbol</tool_name>
# <description>Gets the stock ticker symbol for a company searched by name. Returns str: The ticker symbol for the company stock. Raises TickerNotFound: if no matching ticker symbol is found.</description>
# <parameters>
# <parameter>
# <name>company_name</name>
# <type>string</type>
# <description>The name of the company.</description>
# </parameter>
# </parameters>
# </tool_description>
class ToolParameter:
    def __init__(self, name, tool_type, description):
        self.name = name
        self.tool_type = tool_type
        self.description = description


class Tool:
    def __init__(self, name: str, description: str, parameters: List[ToolParameter], callback: callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.callback = callback

    def get_xml(self):
        parameters = "".join([f"<parameter>\n<name>{param.name}</name>\n<type>{param.tool_type}</type>\n<description>{param.description}</description></parameter>" for param in self.parameters])
        return f"""<tool_description>
<tool_name>{self.name}</tool_name>
<description>
{self.description}
</description>
<parameters>
{parameters}
</parameters>
</tool_description>"""


class FunctionCall:
    # <function_calls>
    # <invoke>
    # <tool_name>get_ticker_symbol</tool_name>
    # <parameters>
    # <company_name>General Motors</company_name>
    # </parameters>
    # </invoke>
    # </function_calls>
    def __init__(self, xml):
        self.xml = xml
        root = ET.fromstring(xml)
        self.name = root.find('tool_name').text.strip()
        self.parameters = {}
        parameters = root.find('parameters')
        if parameters is not None:
            for param in parameters:
                self.parameters[param.tag] = param.text.strip()

    # <function_results>
    # <result>
    # <tool_name>get_ticker_symbol</tool_name>
    # <stdout>
    # GM
    # </stdout>
    # </result>
    # </function_results>
    def invoke(self, tools: List[Tool]) -> str:
        tool = [tool for tool in tools if tool.name == self.name][0]
        if not tool:
            raise ValueError(f"Tool '{self.name}' not found")

        # Call the tool with the parameters
        response = tool.callback(**self.parameters)
        return f"<result>\n<tool_name>{self.name}</tool_name>\n<stdout>{response}</stdout>\n</result>\n"


def get_context(tools: List[Tool]) -> str:
    tool_descriptions = "\n".join([tool.get_xml() for tool in tools])
    return f"""In this environment you have access to a set of tools you can use to answer the user's question.

You may call them like this:
<function_calls>
<invoke>
<tool_name>$TOOL_NAME</tool_name>
<parameters>
<$PARAMETER_NAME>$PARAMETER_VALUE</$PARAMETER_NAME>
...
</parameters>
</invoke>
</function_calls>

Here are the tools available:
<tools>
{tool_descriptions}
</tools>

Here's an example conversation of yours:

<scratchpad>
To answer this question, I will need to:

1. Get the ticker symbol for General Motors using the get_ticker_symbol() function.
2. Use the returned ticker symbol to get the current stock price using the get_current_stock_price() function.
</scratchpad>

<function_calls>
<invoke>
<tool_name>get_ticker_symbol</tool_name>
<parameters>
<company_name>General Motors</company_name>
</parameters>
</invoke>
</function_calls>

Using the scratchpad is mandatory, to provide feedback to the user, and thoroughly explain the steps you are taking to answer their question.
Function calls are optional, but they should be used whenever necessary to answer the user's question.

ONLY COMMUNICATE BACK TO THE USER USING THE SCRATCHPAD. (<scratchpad>...</scratchpad>)
The function calls will be run, and fed back into you.
OUTPUT IN XML.
"""

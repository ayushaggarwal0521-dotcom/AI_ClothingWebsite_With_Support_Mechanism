from app.services.conversation_service import send_customer_message
from app.services.llm_service import (
    create_llm_conversation,
    send_message_to_llm,
    send_tool_result_to_llm,
    acknowledge_tool_call
)
import asyncio
import json
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MCP_SERVER_PATH = str(
    Path(__file__).resolve().parents[2] / "mcp_server" / "server.py"
)


def _server_params():
    # The MCP server runs as a child process. By default it would NOT inherit
    # DATABASE_URL etc., so pass the environment explicitly.
    return StdioServerParameters(
        command=sys.executable,
        args=[MCP_SERVER_PATH],
        env=dict(os.environ)
    )

async def get_mcp_tools():
    server_params = _server_params()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            tools_result = await session.list_tools()

            return tools_result.tools
        
def handle_ask_customer(arguments: dict):
    return {
        "success": True,
        "type": "ASK_CUSTOMER",
        "question": arguments["question"]
    }

def create_ask_customer_tool():
    return {
        "type": "function",
        "name": "ask_customer",
        "description": (
            "Ask the customer for information that is required to continue "
            "their request and cannot be obtained from the available tools."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the customer."
                }
            },
            "required": ["question"],
            "additionalProperties": False
        }
    }

        

def convert_mcp_tools_to_llm_tools(mcp_tools):
    llm_tools = []

    for tool in mcp_tools:
        description = tool.description or ""

        if tool.name == "search_products":
            description += """
            
Important:
Only provide filters that the customer actually specified or that can be
reliably inferred from the customer's request.

For optional filters that the customer did not specify, use null.
Do NOT use values such as "any", "all", "whatever", or "none".

Examples:

"black oversized t-shirts under 2000"
→ color="black", fit="oversized", category="t-shirts",
  max_price=2000
→ gender=null, material=null, size=null

"men's cotton shirts"
→ gender="men", material="cotton", category="shirts"
→ color=null, fit=null, max_price=null, size=null
"""

        llm_tool = {
            "type": "function",
            "name": tool.name,
            "description": description,
            "parameters": tool.input_schema
        }

        llm_tools.append(llm_tool)

    return llm_tools

def extract_tool_call(result):
    for item in result["output"]:
        if item.type == "function_call":
            return {
                "tool_name": item.name,
                "arguments": json.loads(item.arguments),
                "call_id": item.call_id
            }

    return None


async def execute_mcp_tool(tool_name: str, arguments: dict):
    server_params = _server_params()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments
            )

            return result

def parse_mcp_tool_result(tool_result):
    if tool_result.is_error:
        return {
            "success": False,
            "error": "MCP tool execution failed."
        }

    if not tool_result.content:
        return {
            "success": False,
            "error": "MCP tool returned no content."
        }

    for content in tool_result.content:
        if content.type == "text":
            return json.loads(content.text)

    return {
        "success": False,
        "error": "MCP tool returned an unsupported result format."
    }

def normalize_tool_arguments(tool_name: str, arguments: dict):
    if tool_name == "search_products":
        optional_filters = [
            "category",
            "color",
            "gender",
            "material",
            "fit",
            "max_price",
            "size"
        ]

        for field in optional_filters:
            value = arguments.get(field)

            if isinstance(value, str):
                value = value.strip().lower()

                if value in ("", "any", "none", "null"):
                    arguments[field] = None

    return arguments

async def process_message(
        llm_conversation_id: str,
        message: str,
        llm_tools: list
    ):
    result = send_message_to_llm(
        llm_conversation_id,
        message,
        llm_tools
    )
    tool_results = []  # lets the frontend render product cards etc.
    while True:
        tool_call = extract_tool_call(result)
        if not tool_call:
            return {
                "type": "FINAL_RESPONSE",
                "response": result["response"],
                "tool_results": tool_results
            }
        if tool_call["tool_name"] == "ask_customer":
            customer_request = handle_ask_customer(
                tool_call["arguments"]
            )

            acknowledge_tool_call(

                llm_conversation_id,
                tool_call["call_id"],
                customer_request
            )

            customer_request["tool_results"] = tool_results
            return customer_request

    
        normalized_arguments = normalize_tool_arguments(
            tool_call["tool_name"],
            tool_call["arguments"]
        )

        tool_result = await execute_mcp_tool(
            tool_call["tool_name"],
            normalized_arguments
        )

        parsed_result = parse_mcp_tool_result(tool_result)
        tool_results.append({"tool": tool_call["tool_name"], "result": parsed_result})

        result = send_tool_result_to_llm(
            llm_conversation_id,
            tool_call["call_id"],
            parsed_result,
            llm_tools
        )


if __name__ == "__main__":

    mcp_tools = asyncio.run(get_mcp_tools())

    llm_tools = convert_mcp_tools_to_llm_tools(mcp_tools)

    llm_tools.append(create_ask_customer_tool())

    llm_conversation_id = create_llm_conversation()

    result = asyncio.run(
        process_message(
            llm_conversation_id,
            "I want to return a jacket from order ORD-080.",
            llm_tools
        )
    )

    print("\nFIRST MESSAGE RESULT:")
    print(result)


    # result = asyncio.run(
    #     process_message(
    #         llm_conversation_id,
    #         "I want to return 1 Everyday Denim Jacket because of size issue.",
    #         llm_tools
    #     )
    # )

    # print("\nSECOND MESSAGE RESULT:")
    # print(result)


    # second_result = process_message(
    #     llm_conversation_id,
    #     "ORD-080",
    #     llm_tools
    # )

    # print("\nSECOND PROCESS MESSAGE RESULT:") 
    # print(second_result)

# if __name__ == "__main__":
    
#     mcp_tools = asyncio.run(get_mcp_tools())

#     llm_tools = convert_mcp_tools_to_llm_tools(mcp_tools)

#     llm_tools.append(create_ask_customer_tool())

#     llm_conversation_id = create_llm_conversation()

#     message = "I want to cancel my order."

#     result = send_message_to_llm(
#         llm_conversation_id,
#         message,
#         llm_tools
#     )

#     tool_call = extract_tool_call(result)

#     print("\nEXTRACTED TOOL CALL:")
#     print(tool_call)

#     if tool_call:
#         if tool_call["tool_name"] == "ask_customer":
#             customer_request = handle_ask_customer(
#                 tool_call["arguments"]
#             )

#             print("\nASK CUSTOMER:")
#             print(customer_request)

#             acknowledge_tool_call(
#                 llm_conversation_id,
#                 tool_call["call_id"],
#                 customer_request
#             )


#             second_message = "ORD-080"

#             second_result = send_message_to_llm(
#                 llm_conversation_id,
#                 second_message,
#                 llm_tools
#             )

#             print("\nSECOND MESSAGE RESULT:")
#             print(second_result["output"])

#             second_tool_call = extract_tool_call(second_result)

#             print("\nSECOND EXTRACTED TOOL CALL:")
#             print(second_tool_call)



#             if second_tool_call:
#                 normalized_arguments = normalize_tool_arguments(
#                 second_tool_call["tool_name"],
#                 second_tool_call["arguments"]
#             )

#             print("\nSECOND NORMALIZED ARGUMENTS:")
#             print(normalized_arguments)

#             tool_result = asyncio.run(
#                 execute_mcp_tool(
#                     second_tool_call["tool_name"],
#                     normalized_arguments
#                 )
#             )

#             parsed_result = parse_mcp_tool_result(tool_result)

#             print("\nSECOND PARSED MCP RESULT:")
#             print(parsed_result)

#             final_result = send_tool_result_to_llm(
#                 llm_conversation_id,
#                 second_tool_call["call_id"],
#                 parsed_result,
#                 llm_tools
#             )

#             print("\nFINAL LLM RESPONSE:")
#             print(final_result["response"])

#         else:
        
            
#             normalized_arguments = normalize_tool_arguments(
#                 tool_call["tool_name"],
#                 tool_call["arguments"]
#             )

#             print("\nNORMALIZED ARGUMENTS:")
#             print(normalized_arguments)

#             tool_result = asyncio.run(
#                 execute_mcp_tool(
#                     tool_call["tool_name"],
#                     normalized_arguments
#                 )
#             )

#             parsed_result = parse_mcp_tool_result(tool_result)

#             print("\nPARSED MCP RESULT:")
#             print(parsed_result)

#             parsed_result = parse_mcp_tool_result(tool_result)
#             print("\nPARSED MCP RESULT:")
#             print(parsed_result)

#             print("\nRAW TOOL RESULT:")
#             print(tool_result)

#             final_result = send_tool_result_to_llm(
#                 llm_conversation_id,
#                 tool_call["call_id"],
#                 parsed_result,
#                 llm_tools
#             )
#             print("\nRAW FINAL LLM OUTPUT:")
#             print(final_result["output"])






#             print("\nFINAL LLM RESPONSE:")
#             print(final_result["response"])

    

# def process_customer_message(
#     customer_id: str,
#     message_text: str
# ):
#     # Step 1: Handle conversation/business rules
#     conversation_result = send_customer_message(
#         customer_id,
#         message_text
#     )

#     # If the conversation service failed, stop here
#     if not conversation_result["success"]:
#         return conversation_result

#     # If the conversation reached human handoff,
#     # do not send the message to the AI.
#     if conversation_result["status"] == "HUMAN_HANDOFF":
#         return conversation_result

#     # Step 2: Get the OpenAI conversation ID
#     llm_conversation_id = conversation_result["llm_conversation_id"]

#     # Step 3: Send the customer message to OpenAI
#     llm_result = send_message_to_llm(
#         llm_conversation_id,
#         message_text
#     )

#     # Step 4: Return the combined result
#     return {
#         "success": True,
#         "conversation_id": conversation_result["conversation_id"],
#         "llm_conversation_id": llm_conversation_id,
#         "customer_message_id": conversation_result["message_id"],
#         "customer_message": message_text,
#         "ai_response": llm_result["response"],
#         "customer_message_count": conversation_result["customer_message_count"]
#     }
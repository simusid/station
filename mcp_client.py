#!/usr/bin/env python3
import asyncio
import json
import sys
from openai import OpenAI
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

rc = load_dotenv()
if(rc==False):
    print("LLM api keys not found... exiting")
    exit()
try:       
    api_key = os.environ['api_key']
    base_url= os.environ['base_url']
except:
    pass

#api_key="foo"
#base_url = "http://localhost:8080/v1"
base_url=None  # use openai if None

class MCPLLMIntegration:
    def __init__(self, base_url=None):
        # Initialize OpenAI client for llama.cpp server
        self.llm_client = OpenAI(api_key = api_key, base_url=base_url)
        self.mcp_session = None
        self.available_tools = []
        
    async def connect_mcp(self):
        """Connect to MCP server and get available tools"""

        """Adjust these launch parameters as needed to ensure a valid
        python environment (e.g. paths and permissions)"""
        server_params = StdioServerParameters(
            command="zsh",
            args=["/Users/gary/Desktop/station/start_mcp_server.sh"]
        )
        
        print("Connecting to MCP server...")
        self.stdio_client = stdio_client(server_params)
        self.read, self.write = await self.stdio_client.__aenter__()
        self.mcp_session = ClientSession(self.read, self.write)
        await self.mcp_session.__aenter__()
        
        # Initialize and get tools
        await self.mcp_session.initialize()
        tools_response = await self.mcp_session.list_tools()
         
        self.available_tools = tools_response.tools  
        print(f"\n\nConnected! Available MCP tools: {[tool.name for tool in self.available_tools]}","\n\n")
        
    async def disconnect_mcp(self):
        """Clean up MCP connection"""
        if self.mcp_session:
            await self.mcp_session.__aexit__(None, None, None)
        if hasattr(self, 'stdio_client'):
            await self.stdio_client.__aexit__(None, None, None)
    
    def mcp_tools_to_openai_format(self):
        """Convert MCP tools to OpenAI function calling format"""
        openai_tools = []
        for tool in self.available_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"Execute {tool.name} tool",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # Add parameters if the tool has any
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                if hasattr(tool.inputSchema, 'properties'):
                    openai_tool["function"]["parameters"]["properties"] = tool.inputSchema.properties
                if hasattr(tool.inputSchema, 'required'):
                    openai_tool["function"]["parameters"]["required"] = tool.inputSchema.required
                    
            openai_tools.append(openai_tool)
        
        return openai_tools
    
    async def call_mcp_tool(self, tool_name, arguments):
        """Call an MCP tool and return the result"""
        try:
            result = await self.mcp_session.call_tool(tool_name, arguments)
            # Extract text content from result
            content_text = ""
            for content in result.content:
                if hasattr(content, 'text'):
                    content_text += content.text
                else:
                    content_text += str(content)
            return content_text
        except Exception as e:
            return f"Error calling tool {tool_name}: {str(e)}"
    
    async def chat_with_tools(self, user_message, conversation_history=None):
        """Chat with LLM that can call MCP tools"""

        if conversation_history is None:
            conversation_history = []
        
        # Add user message
        messages = conversation_history + [
            {"role": "user", "content": user_message}
        ]
        
        # Get OpenAI-formatted tools
        tools = self.mcp_tools_to_openai_format()
        
        while True:
            # Call LLM
            response = self.llm_client.chat.completions.create(
                model="gpt-4.1",  # This is ignored by llama.cpp but required
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )
            
            assistant_message = response.choices[0].message
            messages.append({
                "role": "assistant", 
                "content": assistant_message.content,
                "tool_calls": assistant_message.tool_calls
            })
            
            # Check if LLM wants to call tools
            if assistant_message.tool_calls:
                print(f"\nLLM wants to call tools: {[tc.function.name for tc in assistant_message.tool_calls]}")
                
                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    print(f"Calling {tool_name} with args: {arguments}")
                    tool_result = await self.call_mcp_tool(tool_name, arguments)
                    print(f"Tool result: {tool_result}")
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # Continue the loop to let LLM respond with the tool results
                continue
            else:
                # No more tool calls, return final response
                return assistant_message.content, messages

async def main():
    integration = MCPLLMIntegration(base_url=base_url)
    
    try:
        # Connect to MCP server
        await integration.connect_mcp()
        
        print("\n=== MCP + LLM Integration Ready ===")
        print("Type 'quit' to exit\n")
        contacts = await integration.mcp_session.read_resource("config://contacts")

        system=f"""You are Station.  You manage the state of an organization.  The state 
        consists of a set of objects, the attributes of those objects, and  the interrelationships 
         between two or more objects.  
          
        You may be asked a question about an object, relationship, or state that you know
         nothing about.  In that case you are to respond by asking for more information.
          
        You are required to save the entire state whenever any object, attribute or relationship
        changes. 
        contact information is:
        {contacts}
        """
        conversation_history = [{"role":"system", "content":system}]
        
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['quit', 'exit']:
                break
                
            print("Assistant: ", end="", flush=True)
            response, conversation_history = await integration.chat_with_tools(
                user_input, 
                conversation_history
            )
            print(response)
            print()
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await integration.disconnect_mcp()

if __name__ == "__main__":
    # Make sure you have llama.cpp server running with:
    # ./server -m your-model.gguf --port 8080
 
    asyncio.run(main())
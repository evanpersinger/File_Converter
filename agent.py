"""
agent.py
This agent is designed to convert files from one format to another.
"""

from agents import Agent, Runner, SQLiteSession, WebSearchTool, function_tool, ModelSettings
from agents.stream_events import RawResponsesStreamEvent
from agents.tracing import set_tracing_disabled
from openai.types.responses import ResponseTextDeltaEvent
# Import conversion functions directly from scripts
from md_pdf import convert_md_to_pdf
from docx_pdf import convert_docx_to_pdf
from txt_pdf import convert_txt_to_pdf
from html_pdf import convert_html_to_pdf
from ipynb_pdf import convert_notebook_to_pdf
from pathlib import Path
import os
import asyncio

# Disable tracing to avoid SSL errors
set_tracing_disabled(True)


agent = Agent(
    
    # name of the agent, you can name it whatever you want
    name="Basic Agent", 
    
    # model the agent uses, you can use any model you want
    model="gpt-5-nano", 
    
    # tools the agent can use, you can add more tools here, some tools have 
    # any tools defined here, also needs to be imported from the agents package
    tools=[
        
        # regular web search tool, no parameters needed
        WebSearchTool(), 
        
        # Conversion functions as tools
        function_tool(convert_md_to_pdf),
        function_tool(convert_docx_to_pdf),
        function_tool(convert_txt_to_pdf),
        function_tool(convert_html_to_pdf),
        function_tool(convert_notebook_to_pdf),
        
        ], 
    
    
    
    # controls how the model behaves
    # Note: gpt-5-nano doesn't support temperature parameter
    model_settings=ModelSettings(
        # max_tokens limits the number of tokens the agent can use in a conversation, used to prevent the agent from using too many tokens
        max_tokens=1000,
        
        # tool choice allows you to demand that the agent uses a specific tool
        # "read_file" means the agent will use the read_file tool
        # tool_choice="read_file",
        
        # tool use behavior controls how tool output is handled
        # "stop_on_first_tool" means the agent will stop after the first tool call
        # tool_use_behavior="stop_on_first_tool",
        
        
        
    ),
    
    
    # instructions for the agent, you can change this to whatever you want
    instructions=
    """
    You are an AI Agent that can convert files from one format to another.
    
    Available conversion functions:
    - convert_md_to_pdf: Convert Markdown (.md) files to PDF
    - convert_docx_to_pdf: Convert Word (.docx) files to PDF
    - convert_txt_to_pdf: Convert Text (.txt) files to PDF
    - convert_html_to_pdf: Convert HTML files to PDF
    - convert_notebook_to_pdf: Convert Jupyter Notebook (.ipynb) files to PDF
    - web_search: Search the web for information
    
    When a user asks to convert a file:
    1. Use the appropriate conversion function with the filename from the input folder
    2. You can optionally specify an output filename
    3. Confirm the conversion was successful
    
    Files should be in the 'input' folder and will be saved to the 'output' folder.
    """, 
    
)




# main function
# this is the main function that will be called to run the agent
async def main():
    # Sessions store conversation history so the agent remembers previous messages
    session = SQLiteSession(session_id="example_session")
    
    print("Type 'quit' or 'exit' to stop.\n")
    
    # Interactive loop to ask questions
    while True:
        try:
            # Get user input
            user_input = input(f"{agent.name}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye")
            break
        
        # Check if user wants to quit
        # if the user inputs 'quit', 'exit', or 'q', the session will end
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Session ended")
            break
        
        # Skip empty inputs
        if not user_input:
            continue
        
        # Run the agent with streaming (shows response as it's generated)
        print("\nAgent: ", end="", flush=True)
        result = Runner.run_streamed(agent, user_input, session=session)
        
        # Stream the response in real-time
        async for event in result.stream_events():
            if isinstance(event, RawResponsesStreamEvent):
                if isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)
        
        print("\n")  # Add newline after response



# run the agent
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        print("\nSession ended")
    
    

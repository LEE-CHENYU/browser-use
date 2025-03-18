from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

async def main():
    # Make sure you have your OpenAI API key in your .env file
    if not os.getenv("OPENAI_API_KEY"):
        print("Please add your OPENAI_API_KEY to the .env file")
        return
    
    # Create an agent with a specific task to navigate yingjiesheng.com
    # Include detailed instructions for handling login popups
    agent = Agent(
        task="""
        Navigate to yingjiesheng.com and explore the website.
        
        First, if a login popup appears, close it by clicking the X button or the Close button.
        
        Then, explore the following areas:
        1. Job listings - Look at available job postings
        2. Forums - Browse discussion forums if available
        3. Other features - Explore any other interesting features on the site
        
        Take screenshots of interesting pages.
        
        If you encounter any login walls or popups during exploration, close them if possible or skip those sections and explore the publicly accessible parts of the site.
        """,
        llm=ChatOpenAI(model="gpt-4o")
    )
    
    # Run the agent
    result = await agent.run()
    
    # Print the result
    print("Agent completed with result:", result)

if __name__ == "__main__":
    asyncio.run(main()) 
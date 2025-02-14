import streamlit as st
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import List
class QuoraUserInteractionSchema(BaseModel):
    username: str = Field(description="Username of poster")
    bio: str = Field(description="User bio")
    post_type: str = Field(description="Type: question/answer")
    timestamp: str = Field(description="Post time")
    upvotes: int = Field(default=0)

def search_for_urls(company_description: str, firecrawl_api_key: str, num_links: int)->List[str]:
    url = "https://api.firecrawl.dev/v1/search"
    payload = {
        "query": f"quora websites where people are looking for {company_description}",
        "limit": num_links,
        "lang": "en",
        "location": "United States"
    }
    response = requests.post(url, json=payload, headers={
        "Authorization": f"Bearer {firecrawl_api_key}"
    })


def extract_user_info_from_urls(urls: List[str], firecrawl_api_key: str) -> List[dict]:
    firecrawl_app = FirecrawlApp(api_key=firecrawl_api_key)

    for url in urls:
        response = firecrawl_app.extract(
            [url],
            {
                     'prompt': 'Extract user information from Quora posts',
                     'schema': QuoraPageSchema.model_json_schema(),
                    }
        )

def format_user_info_to_flattened_json(user_info_list: List[dict]) -> List[dict]:
    flattened_data = []
    for info in user_info_list:
        for interaction in info["user_info"]:
            flattened_data.append({
                "Website URL": info["website_url"],
                "Username": interaction.get("username", ""),
                "Bio": interaction.get("bio", ""),
                # Add other fields...
            })


def create_google_sheets_agent(composio_api_key: str, openai_api_key: str) -> Agent:
    composio_toolset = ComposioToolSet(api_key=composio_api_key)
    google_sheets_tool = composio_toolset.get_tools(
        actions=[Action.GOOGLESHEETS_SHEET_FROM_JSON]
    )[0]

    return Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        tools=[google_sheets_tool],
        system_prompt="Create Google Sheets from JSON data"
    )


def write_to_google_sheets(flattened_data: List[dict], composio_api_key: str, openai_api_key: str) -> str:
    google_sheets_agent = create_google_sheets_agent(composio_api_key, openai_api_key)

    message = (
        "Create a new Google Sheet with columns: "
        "Website URL, Username, Bio, Post Type, Timestamp, Upvotes, Links\n\n"
        f"{json.dumps(flattened_data, indent=2)}"
    )

def create_prompt_transformation_agent(openai_api_key: str) -> Agent:
    return Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        system_prompt="""Transform detailed queries into concise descriptions
Example:
Input: "Looking for AI video editing software users"
Output: "AI video editing software"
"""
    )


def main():
    st.title("🎯 AI Lead Generation Agent")

    with st.sidebar:
        st.header("API Keys")
        firecrawl_api_key = st.text_input("Firecrawl API Key")
        openai_api_key = st.text_input("OpenAI API Key")
        composio_api_key = st.text_input("Composio API Key")

user_query = st.text_area(
    "Describe what leads you're looking for:",
    placeholder="e.g., Looking for AI video editing software users"
)

num_links = st.number_input(
    "Number of links to search",
    min_value=1,
    max_value=10
)

if st.button("Generate Leads"):
    # Transform query
    transform_agent = create_prompt_transformation_agent(openai_api_key)
    company_description = transform_agent.run(user_query)

    # Search URLs
    urls = search_for_urls(company_description.content, firecrawl_api_key)

    # Extract and process info
    user_info_list = extract_user_info_from_urls(urls, firecrawl_api_key)

with st.spinner("Processing your query..."):
    st.write("🎯 Searching for:", company_description.content)

with st.spinner("Searching URLs..."):
    user_info_list = extract_user_info_from_urls(urls, firecrawl_api_key)
    st.write(f"Extracted {len(user_info_list)} user profiles.")
    # URL search code...

with st.spinner("Extracting info..."):
    # Info extraction code...

    if urls:
        st.subheader("Quora Links Used:")
        for url in urls:
            st.write(url)

        if google_sheets_link:
            st.success("Lead generation completed!")
            st.markdown(f"[View Sheet]({google_sheets_link})")

if not all([firecrawl_api_key, openai_api_key, composio_api_key]):
    st.error("Please fill in all API keys.")

try:
    # Process workflow
     pass
except Exception as e:
    st.error(f"Error: {str(e)}")
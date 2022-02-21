import slack
import os
import json
import requests
from pydantic import BaseModel
from typing import List, Optional
from requests.auth import HTTPBasicAuth
from fastapi import FastAPI, Form
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

slack_token = os.getenv("SLACK_TOKEN")
jira_url = os.getenv("JIRA_URL")
jira_username = os.getenv("JIRA_USERNAME")
jira_token = os.getenv("JIRA_TOKEN")
client = slack.WebClient(token=slack_token)

class JiraSearchResults(BaseModel):
    expand: str
    startAt: int
    maxResults: int
    total: int
    issues: List[dict]
    warningMessages: Optional[List[str]]

@app.get("/send-message")
def send_test_message():
    client.chat_postMessage(channel='travl', text='suh dude')
    return {
        "message": "Test Message Sent Successfully"
    }

@app.post("/slash/gimme")
def slash_command_test(api_app_id: str = Form(...), text: str = Form(...), command: str = Form(...), user_id: str = Form(...), user_name: str = Form(...),
    channel_id: str = Form(...), channel_name: str = Form(...)):

    print(api_app_id, text, command, user_id, user_name, channel_id, channel_name)

    return "done"

@app.post("/jira", response_model=JiraSearchResults)
def search_jira(query: str):
    url = f"{jira_url}/search"
    auth = HTTPBasicAuth(jira_username, jira_token)

    headers = {
        "Accept": "application/json"
    }

    query = {
        'jql': f'project = TRAVL AND text ~ {query}'
    }

    response = requests.request(
        "GET",
        url,
        headers=headers,
        params=query,
        auth=auth
    )

    data = json.loads(response.text)

    return data

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
jira_api_url = os.getenv("JIRA_API_URL")
jira_ui_url = os.getenv("JIRA_UI_URL")
jira_username = os.getenv("JIRA_USERNAME")
jira_token = "3tKP91W2cYw9XHBpRGW6C331"
postman_token = "PMAK-637f797df599196a8be5f5e0-4cc556d223abe02774730a3248dafab28d"
dropbox_key = "57lukiw9m67st9h"
dropbox_secret = "gm8rq2h9ck7bs72"
dropbox_token = "sl.BTtDDRN2asc--P-Y3P_6tO9HFxe2hfz-_YjFFkdv_ckyXcbiQDXbgXsm9FsrHOnN8B5tCk1WR340BSd7zqbfNA1VupmRr4vYbQPPMIJbN0OnpC65xAhvVrS4ep9noixyseDNqqp"

client = slack.WebClient(token=slack_token)

class JiraSearchResults(BaseModel):
    expand: Optional[str]
    startAt: int
    maxResults: int
    total: int
    issues: Optional[List[dict]]
    warningMessages: Optional[List[str]]

class JiraSanitisedTicket(BaseModel):
    issue_key: str
    url: str
    summary: str
    status: str

class JiraSanitisedResults(BaseModel):
    total: int
    results: List[JiraSanitisedTicket]

def send_message():
    client.chat_postMessage(channel='travl', text='suh dude')
    return {
        "message": "Test Message Sent Successfully"
    }

@app.post("/jira-search")
def jira_search(text: str = Form(...)):
    params = text.split(None, 1)
    if len(params) < 2: return "Please provide both the Project Key and Search Query."
    # if params[0] != "LIVE" or params[0] != "IDEA": return "Sorry, we currently only support LIVE or IDEA searches."
    if params[0] != "TRAVL": return "Sorry, we currently only support LIVE or IDEA searches."
    query = params[1]
    result = search_jira(params[0], query)
    response_message = build_jira_message(result.total, params[0], query, result.results)

    return response_message

def search_jira(project_key: str, query: str) -> JiraSanitisedResults: 
    url = f"{jira_api_url}/search"
    auth = HTTPBasicAuth(jira_username, jira_token)

    headers = {
        "Accept": "application/json"
    }

    query = {
        'jql': f"project = {project_key} AND text ~ '{query}'",
        'maxResults': 10,
        'fields': 'key,self,summary,status'
    }

    response = requests.request(
        "GET",
        url,
        headers=headers,
        params=query,
        auth=auth
    )

    data = JiraSearchResults.parse_obj(json.loads(response.text))
    
    if data.total == 0: return JiraSanitisedResults(
        total=0,
        results=[]
    )

    results = []
    for issue in data.issues:
        results.append(JiraSanitisedTicket(
            issue_key=issue["key"],
            url=f'{jira_ui_url}/browse/{issue["key"]}',
            summary=issue["fields"]["summary"],
            status=issue["fields"]["status"]["name"]
        ))
    
    return JiraSanitisedResults(
        total=data.total,
        results=results
    )

def build_jira_message(total: int, project_key: str, query: str, issues: List[JiraSanitisedTicket]):
    
    markdown_text = ""

    for issue in issues:
        markdown_text += f"<{issue.url}|{issue.issue_key}> - {issue.summary} - *{issue.status}*\n"

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Here are the first {total} results for your query"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "plain_text",
                        "text": f"Project Key: {project_key}"
                    },
                    {
                        "type": "plain_text",
                        "text": f"Query: '{query}'"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": markdown_text
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "View all results here:"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Click Me"
                    },
                    "value": "click_me_827",
                    "url": f"{jira_ui_url}/issues/?jql=project%20=%20{project_key}%20AND%20text%20~%20'{query}'",
                    "action_id": "button-action"
                }
            }
        ]
    }
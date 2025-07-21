from azure.ai.agents.models import FunctionTool
import requests
import os
from base64 import b64encode
from html import unescape
import json

class AzureDevOpsTool:
    def __init__(self, organization: str, project: str):
        self.organization = organization
        self.project = project
        self.api_version = "7.1-preview.3"
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis"

        pat = os.getenv("ADO_PAT")
        if not pat:
            raise ValueError("ADO_PAT environment variable is not set")
        self.auth_header = {
            "Authorization": f"Basic {b64encode(f':{pat}'.encode()).decode()}"
        }
        
        self._tool = FunctionTool({self.get_azure_devops_story})

    @property
    def definitions(self):
        return self._tool.definitions

    def get_azure_devops_story(self, story_id: str) -> str:
        """Get a user story's title, description, state, dates, and assignee from Azure DevOps.
        
        Args:
            story_id: The ID of the Azure DevOps user story to retrieve.
            
        Returns:
            str: Formatted summary of the user story details.
        """
        url = f"{self.base_url}/wit/workitems/{story_id}?api-version={self.api_version}"
        try:
            resp = requests.get(url, headers=self.auth_header)
            resp.raise_for_status()
            fields = resp.json()["fields"]

            title = fields.get("System.Title", "No title")
            state = fields.get("System.State", "Unknown")
            assigned_to = fields.get("System.AssignedTo", {}).get("displayName", "Unassigned")
            created = fields.get("System.CreatedDate", "N/A")
            changed = fields.get("System.ChangedDate", "N/A")
            start_date = fields.get("Microsoft.VSTS.Scheduling.StartDate", "N/A")
            finish_date = fields.get("Microsoft.VSTS.Scheduling.FinishDate", "N/A")
            priority = fields.get("Microsoft.VSTS.Common.Priority", "N/A")
            acceptance = fields.get("Microsoft.VSTS.Common.AcceptanceCriteria", "N/A")
            raw_description = fields.get("System.Description", "No description")

            try:
                from bs4 import BeautifulSoup
                description = unescape(BeautifulSoup(raw_description, "html.parser").get_text(strip=True))
            except ImportError:
                import re
                description = unescape(re.sub('<[^<]+?>', '', raw_description))

            summary = (
                f"**Story {story_id}: {title}**\n"
                f"- **State:** {state}\n"
                f"- **Assigned To:** {assigned_to}\n"
                f"- **Created:** {created}\n"
                f"- **Last Modified:** {changed}\n"
                f"- **Start Date:** {start_date}\n"
                f"- **Finish Date:** {finish_date}\n"
                f"- **Priority:** {priority}\n"
                f"- **Acceptance Criteria:** {acceptance}\n"
                f"- **Description:**\n{description}"
            )
            return summary

        except Exception as e:
            return f"Failed to retrieve story {story_id}: {e}"


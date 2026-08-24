"""
Microsoft SharePoint uploader for the newsletter.
Uses MSAL for OAuth2 authentication + SharePoint REST API.
"""

import logging
import os
from pathlib import Path

import msal
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class SharePointUploader:
    """
    Uploads newsletter HTML files to a Microsoft SharePoint document library.

    Required env vars:
        SHAREPOINT_SITE_URL      e.g. https://contoso.sharepoint.com/sites/MarketIntel
        SHAREPOINT_CLIENT_ID     Azure App Registration client ID
        SHAREPOINT_CLIENT_SECRET Azure App Registration client secret
        SHAREPOINT_TENANT_ID     Azure tenant ID

    Example:
        uploader = SharePointUploader()
        uploader.upload(Path("newsletter_2025_W24.html"), folder="Market Intelligence/Newsletters")
    """

    GRAPH_API = "https://graph.microsoft.com/v1.0"
    SCOPE = ["https://graph.microsoft.com/.default"]

    def __init__(self):
        self.site_url = os.getenv("SHAREPOINT_SITE_URL", "")
        self.client_id = os.getenv("SHAREPOINT_CLIENT_ID", "")
        self.client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET", "")
        self.tenant_id = os.getenv("SHAREPOINT_TENANT_ID", "")
        self._token: str | None = None

    def _get_token(self) -> str:
        """Acquire OAuth2 token via MSAL client credentials flow."""
        app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
        )
        result = app.acquire_token_for_client(scopes=self.SCOPE)

        if "access_token" not in result:
            raise ValueError(
                f"Failed to acquire token: {result.get('error_description', 'Unknown error')}"
            )
        return result["access_token"]

    def _get_site_id(self, token: str) -> str:
        """Resolve SharePoint site URL to Graph API site ID."""
        # Extract hostname and site path from URL
        # e.g. https://contoso.sharepoint.com/sites/MarketIntel
        parts = self.site_url.replace("https://", "").split("/")
        hostname = parts[0]
        site_path = "/".join(parts[1:])

        url = f"{self.GRAPH_API}/sites/{hostname}:/{site_path}"
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
        return resp.json()["id"]

    def upload(
        self,
        file_path: Path,
        folder: str = "Market Intelligence/Newsletters",
        overwrite: bool = True,
    ) -> str:
        """
        Upload a file to SharePoint.

        Args:
            file_path: Local path to the HTML newsletter
            folder: Target folder path in SharePoint document library
            overwrite: Whether to overwrite existing file

        Returns:
            SharePoint URL of the uploaded file
        """
        if not all([self.client_id, self.client_secret, self.tenant_id, self.site_url]):
            logger.warning("SharePoint credentials not configured. Skipping upload.")
            return ""

        try:
            token = self._get_token()
            site_id = self._get_site_id(token)
            filename = file_path.name
            content = file_path.read_bytes()

            # Upload via Graph API
            upload_url = (
                f"{self.GRAPH_API}/sites/{site_id}/drive/root:/"
                f"{folder}/{filename}:/content"
            )

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "text/html",
            }

            params = {"@microsoft.graph.conflictBehavior": "replace" if overwrite else "fail"}
            resp = requests.put(upload_url, headers=headers, params=params, data=content)
            resp.raise_for_status()

            web_url = resp.json().get("webUrl", "")
            logger.info(f"✅ Uploaded to SharePoint: {web_url}")
            return web_url

        except Exception as e:
            logger.error(f"SharePoint upload failed: {e}")
            raise

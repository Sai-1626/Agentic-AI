"""
Social Media Publishing Integrations for YouTube and Instagram.
Implements Modules 6 Parts K and L (Nodes 26, 27, 28, 29, 30, 31, 32)
of the Agentic AI Video Creation System.
"""

import os
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import requests

from .config import Config

logger = logging.getLogger(__name__)

class YouTubePublisher:
    """Official YouTube Data API v3 video uploader."""

    @classmethod
    def upload(
        cls,
        video_path: Path,
        title: str,
        description: str,
        tags: list,
        privacy_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Uploads a video to YouTube using OAuth credentials or structured dry-run simulation.
        """
        privacy = privacy_status or Config.YOUTUBE_DEFAULT_PRIVACY
        logger.info(f"YouTubePublisher preparing upload for: {video_path} (privacy: {privacy})")

        if not video_path.exists():
            return {
                "status": "error",
                "error": f"Video file not found: {video_path}",
                "youtube_url": None
            }

        # Check for real Google API client and token
        token_path = Path(Config.YOUTUBE_CREDENTIALS_FILE)
        client_secrets = Path(Config.YOUTUBE_CLIENT_SECRETS_FILE)

        if not Config.DRY_RUN_PUBLISHING and token_path.exists() and client_secrets.exists():
            try:
                # Real OAuth upload
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                from googleapiclient.http import MediaFileUpload

                creds = Credentials.from_authorized_user_file(str(token_path), ["https://www.googleapis.com/auth/youtube.upload"])
                youtube = build("youtube", "v3", credentials=creds)

                body = {
                    "snippet": {
                        "title": title[:100],
                        "description": description[:5000],
                        "tags": tags[:20],
                        "categoryId": "27"  # Education
                    },
                    "status": {
                        "privacyStatus": privacy
                    }
                }
                media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
                request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
                response = request.execute()

                video_id = response.get("id")
                video_url = f"https://youtube.com/shorts/{video_id}"
                logger.info(f"Successfully uploaded to YouTube: {video_url}")
                return {
                    "status": "success",
                    "mode": "live",
                    "video_id": video_id,
                    "youtube_url": video_url,
                    "privacy": privacy
                }
            except Exception as e:
                logger.error(f"YouTube upload failed: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "youtube_url": None
                }

        # Safe dry-run / mock testing mode
        mock_id = f"yt_{uuid.uuid4().hex[:11]}"
        mock_url = f"https://youtube.com/shorts/{mock_id}"
        logger.info(f"YouTube dry-run mode active. Simulated upload: {mock_url}")
        return {
            "status": "success",
            "mode": "dry_run",
            "video_id": mock_id,
            "youtube_url": mock_url,
            "privacy": privacy,
            "note": "Uploaded in dry-run mode. Configure client_secrets.json and DRY_RUN_PUBLISHING=false for live upload."
        }


class InstagramPublisher:
    """Official Meta Graph API v21.0 Instagram Reels publisher."""

    @classmethod
    def create_media_container(cls, video_url: str, caption: str) -> Dict[str, Any]:
        """
        Step 1: Node 28 - Create Instagram Reel media container.
        """
        if not Config.DRY_RUN_PUBLISHING and Config.INSTAGRAM_ACCESS_TOKEN and Config.INSTAGRAM_BUSINESS_ACCOUNT_ID:
            endpoint = f"https://graph.facebook.com/{Config.INSTAGRAM_GRAPH_VERSION}/{Config.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
            payload = {
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": Config.INSTAGRAM_ACCESS_TOKEN
            }
            try:
                resp = requests.post(endpoint, data=payload, timeout=30)
                data = resp.json()
                if "id" in data:
                    return {"status": "success", "container_id": data["id"]}
                return {"status": "error", "error": data.get("error", {}).get("message", "Container creation failed")}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        # Dry run simulation
        mock_container_id = f"container_{uuid.uuid4().hex[:12]}"
        return {"status": "success", "container_id": mock_container_id, "mode": "dry_run"}

    @classmethod
    def check_container_status(cls, container_id: str) -> Dict[str, Any]:
        """
        Step 2: Node 30 - Check processing status of the container.
        """
        if not Config.DRY_RUN_PUBLISHING and Config.INSTAGRAM_ACCESS_TOKEN:
            endpoint = f"https://graph.facebook.com/{Config.INSTAGRAM_GRAPH_VERSION}/{container_id}"
            params = {
                "fields": "status_code,status",
                "access_token": Config.INSTAGRAM_ACCESS_TOKEN
            }
            try:
                resp = requests.get(endpoint, params=params, timeout=15)
                data = resp.json()
                status_code = data.get("status_code", "IN_PROGRESS")
                return {"status": "success", "status_code": status_code}
            except Exception as e:
                return {"status": "error", "error": str(e), "status_code": "ERROR"}

        # Dry run returns FINISHED immediately
        return {"status": "success", "status_code": "FINISHED", "mode": "dry_run"}

    @classmethod
    def publish_container(cls, container_id: str) -> Dict[str, Any]:
        """
        Step 3: Node 32 - Publish the Instagram Reel.
        """
        if not Config.DRY_RUN_PUBLISHING and Config.INSTAGRAM_ACCESS_TOKEN and Config.INSTAGRAM_BUSINESS_ACCOUNT_ID:
            endpoint = f"https://graph.facebook.com/{Config.INSTAGRAM_GRAPH_VERSION}/{Config.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
            payload = {
                "creation_id": container_id,
                "access_token": Config.INSTAGRAM_ACCESS_TOKEN
            }
            try:
                resp = requests.post(endpoint, data=payload, timeout=30)
                data = resp.json()
                if "id" in data:
                    post_id = data["id"]
                    return {
                        "status": "success",
                        "post_id": post_id,
                        "instagram_url": f"https://www.instagram.com/reel/{post_id}/"
                    }
                return {"status": "error", "error": data.get("error", {}).get("message", "Publish failed")}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        mock_post_id = f"ig_{uuid.uuid4().hex[:10]}"
        return {
            "status": "success",
            "post_id": mock_post_id,
            "instagram_url": f"https://www.instagram.com/reel/{mock_post_id}/",
            "mode": "dry_run"
        }

    @classmethod
    def publish(cls, video_path: Path, caption: str, hashtags: list) -> Dict[str, Any]:
        """
        Executes full 3-step publishing flow for Instagram Reels.
        """
        full_caption = f"{caption}\n\n{' '.join(hashtags)}"
        video_filename = video_path.name
        hosted_url = f"{Config.HOSTED_MEDIA_BASE_URL}/videos/{video_filename}"

        # 1. Create container
        c_res = cls.create_media_container(hosted_url, full_caption)
        if c_res.get("status") != "success":
            return {"status": "error", "error": c_res.get("error"), "instagram_url": None}

        container_id = c_res["container_id"]

        # 2. Check status loop
        is_ready = False
        for _ in range(5):
            stat = cls.check_container_status(container_id)
            if stat.get("status_code") == "FINISHED":
                is_ready = True
                break
            time.sleep(2)

        if not is_ready:
            return {"status": "error", "error": "Instagram media container timed out or encountered processing error", "instagram_url": None}

        # 3. Publish
        pub_res = cls.publish_container(container_id)
        return pub_res


if __name__ == "__main__":
    yt_res = YouTubePublisher.upload(Path("test.mp4"), "Test Title", "Desc", ["tag"])
    print("YouTube:", yt_res)
    ig_res = InstagramPublisher.publish(Path("test.mp4"), "Test Reel", ["#ai"])
    print("Instagram:", ig_res)

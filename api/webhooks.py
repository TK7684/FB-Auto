"""
Webhook API endpoints for Facebook.

This module handles:
1. Webhook verification (GET /webhook)
2. Incoming message/comment processing (POST /webhook)
"""

from fastapi import APIRouter, Request, Response, BackgroundTasks, HTTPException
from loguru import logger
from typing import Dict, Any, TYPE_CHECKING
from config.settings import settings
from utils.filters import is_relevant_post, is_ignored_user
import json
import time
from datetime import datetime
from pathlib import Path

STATUS_FILE = Path("data/status_chat.json")

def save_chat_status(action: str = "processed"):
    """Save chat bot status."""
    try:
        data = {
            "bot_type": "chat",
            "bot_name": "Chat Operator",
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active",
            "timestamp": time.time(),
            "last_action": action
        }
        STATUS_FILE.parent.mkdir(exist_ok=True)
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save chat status: {e}")

# Use deferred import to avoid circular dependency
# main module is imported inside functions that need it
if TYPE_CHECKING:
    import main

router = APIRouter()


@router.get("/", summary="Verify webhook with Facebook")
async def verify_webhook(
    request: Request
):
    """
    Verify webhook subscription with Facebook.

    Facebook sends a GET request with:
    - hub.mode: Should be "subscribe"
    - hub.verify_token: Should match our VERIFY_TOKEN
    - hub.challenge: Challenge string to return

    Returns the challenge if verification successful.
    """
    # Get query parameters - Facebook uses hub.mode, hub.verify_token, hub.challenge
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    logger.info(f"Webhook verification request: mode={mode}, token={token[:10] if token else 'None'}...")

    import main as main_module
    
    if main_module.facebook_service and mode and token and challenge:
        result = main_module.facebook_service.verify_webhook(mode, token, challenge)
        if result:
            return Response(content=result, status_code=200)

    logger.warning("Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/", summary="Receive Facebook events")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming Facebook events (messages, comments).

    Processes the payload in background to respond quickly to Facebook.
    """
    try:
        payload = await request.json()
        logger.info(f"Received webhook payload with {len(payload.get('entry', []))} entries")

        # Process in background task
        background_tasks.add_task(process_webhook_payload, payload)

        # Return 200 OK immediately (Facebook expects quick response)
        return Response(status_code=200)

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        # Still return 200 to avoid Facebook resending
        return Response(status_code=200)


async def process_webhook_payload(payload: Dict[str, Any]):
    """
    Process webhook payload in background.

    Handles both messaging events and comment events.
    """
    try:
        for entry in payload.get("entry", []):
            entry_id = entry.get("id")
            entry_time = entry.get("time")

            logger.debug(f"Processing entry: {entry_id}")

            # Process messaging events (DMs)
            for messaging in entry.get("messaging", []):
                await process_messaging_event(messaging)

            # Process feed/comment events
            for change in entry.get("changes", []):
                await process_feed_change(change)

    except Exception as e:
        logger.error(f"Error processing webhook payload: {e}")


async def process_messaging_event(messaging: Dict[str, Any]):
    """
    Process a messaging event (DM).

    Args:
        messaging: Messaging event data
    """
    try:
        sender_id = messaging.get("sender", {}).get("id")
        recipient_id = messaging.get("recipient", {}).get("id")

        if not sender_id:
            logger.warning("No sender ID in messaging event")
            return

        # Check if this is a message
        message = messaging.get("message", {})

        # Skip if this is a message echo (our own message)
        if message.get("is_echo"):
            logger.debug(f"Skipping echo message from {sender_id}")
            return

        # Skip if no text content
        message_text = message.get("text", "")
        if not message_text:
            logger.debug(f"No text in message from {sender_id}")
            return

        logger.info(f"📨 Message from {sender_id}: {message_text[:100]}...")

        # Check feature flag
        if not settings.enable_dm_replies:
            logger.info("DM replies disabled, skipping")
            return

        # Handle the message
        await handle_incoming_message(sender_id, message_text)

    except Exception as e:
        logger.error(f"Error processing messaging event: {e}")


async def process_feed_change(change: Dict[str, Any]):
    """
    Process a feed/comment change event.

    Args:
        change: Change event data
    """
    try:
        field = change.get("field")
        value = change.get("value", {})

        logger.debug(f"Feed change: field={field}")

        # Process comment changes
        if field == "feed":
            # Check if this is a comment (not a post)
            if "comment_id" in value and "message" in value:
                comment_id = value["comment_id"]
                comment_text = value["message"]
                post_id = value.get("post_id")
                
                # Extract user name from the payload if available
                user_name = value.get("from", {}).get("name", "")

                logger.info(f"💬 Comment {comment_id} on post {post_id} from {user_name}: {comment_text[:100]}...")
                
                # Check ignored user
                if is_ignored_user(user_name):
                    logger.info(f"Skipping comment from ignored user: {user_name}")
                    return

                # Check feature flag
                if not settings.enable_comment_replies:
                    logger.info("Comment replies disabled, skipping")
                    return

                # Handle the comment with post context
                await handle_comment(comment_id, comment_text, post_id)

            # Check if this is a new post
            elif "post_id" in value and "message" in value:
                post_id = value["post_id"]
                post_message = value["message"]

                logger.info(f"📝 New post {post_id}: {post_message[:100]}...")
                # Could trigger auto-scraper here

    except Exception as e:
        logger.error(f"Error processing feed change: {e}")


async def handle_incoming_message(sender_id: str, message_text: str):
    """
    Handle an incoming DM message.

    Args:
        sender_id: Facebook user ID
        message_text: Message text
    """
    import main as main_module
    
    try:
        # Generate context from knowledge base
        logger.debug(f"Searching knowledge base for: {message_text[:50]}...")
        context = main_module.knowledge_base.generate_context(
            message_text,
            include_qa=True,
            top_products=3,
            top_qa=2
        )

        # Generate response using Gemini
        logger.debug("Generating AI response...")
        response = await main_module.gemini_service.generate_response(
            message_text,
            context
        )

        logger.info(f"Generated response: {response[:100]}...")

        # Send reply via Facebook
        success = await main_module.facebook_service.send_message(sender_id, response)

        if success:
            logger.info(f"✓ Reply sent to {sender_id}")
            save_chat_status(action=f"Replied to {sender_id}")

            # Log to Google Sheets
            try:
                from services.sheets_logger import log_to_sheet
                log_to_sheet(
                    bot_name="Chat Operator",
                    action="DM Reply",
                    user_name=f"User {sender_id}",
                    user_message=message_text,
                    bot_reply=response,
                    status="success"
                )
            except Exception as e:
                logger.error(f"Failed to log chat: {e}")

            # Optionally save Q&A to knowledge base
            main_module.knowledge_base.add_qa_pair(
                question=message_text,
                answer=response,
                source="dm"
            )

            # Save to Memory Service (Tone Learning)
            try:
                main_module.gemini_service.memory_service.add_memory(
                    question=message_text,
                    answer=response,
                    category="marketing"
                )
            except Exception as e:
                logger.error(f"Failed to save chat memory: {e}")
        else:
            logger.error(f"✗ Failed to send reply to {sender_id}")

    except Exception as e:
        logger.error(f"Error handling message: {e}")


    except Exception as e:
        logger.error(f"Error handling comment: {e}")


async def handle_comment(comment_id: str, comment_text: str, post_id: str = None):
    """
    Handle a page comment with post context awareness.
    
    Args:
        comment_id: Facebook comment ID
        comment_text: Comment text
        post_id: Facebook post ID (to fetch caption for context)
    """
    import main as main_module
    
    try:
        # 1. STRICT FILTER: Check for purchase intent keywords first
        if not main_module.gemini_service._is_purchase_intent(comment_text):
            logger.info(f"Skipping comment (no purchase intent): {comment_text[:50]}...")
            return

        # Fetch post caption for context
        post_caption = ""
        if post_id and main_module.facebook_service:
            post_details = main_module.facebook_service.get_post_details(post_id)
            post_caption = post_details.get("message", "")
            logger.debug(f"Post context: {post_caption[:100]}...")

        # FILTER: Check if post is relevant (shared logic)
        if not is_relevant_post(post_caption):
            logger.info(f"Skipping comment on irrelevant post: {post_caption[:30]}...")
            return

        # Generate context from knowledge base
        logger.debug(f"Searching knowledge base for: {comment_text[:50]}...")
        context = main_module.knowledge_base.generate_context(
            comment_text,
            include_qa=True,
            top_products=3,
            top_qa=2
        )

        # Add post caption to context
        if post_caption:
            context = f"บริบทโพสต์: {post_caption}\n\n{context}"

        # Generate response using Gemini
        logger.debug("Generating AI response...")
        response = await main_module.gemini_service.generate_response(
            comment_text,
            context
        )

        logger.info(f"Generated response: {response[:100]}...")

        # Send reply via Facebook
        success = await main_module.facebook_service.send_comment_reply(comment_id, response)

        if success:
            logger.info(f"✓ Reply sent to comment {comment_id}")

            # Log to Google Sheets
            try:
                from services.sheets_logger import log_to_sheet
                log_to_sheet(
                    bot_name="Comment Bot (Webhook)",
                    action="Comment Reply",
                    user_name=f"User", # Name not always available
                    user_message=comment_text,
                    bot_reply=response,
                    comment_id=comment_id,
                    post_id=post_id,
                    status="success"
                )
            except Exception as e:
                logger.error(f"Failed to log comment: {e}")

            # Save to Memory Service (Keep learning)
            try:
                main_module.gemini_service.memory_service.add_memory(
                    question=comment_text,
                    answer=response,
                    category="product"
                )
                logger.debug("Saved interaction to memory.json")
            except Exception as e:
                logger.error(f"Failed to save memory: {e}")

            # Optionally save Q&A to knowledge base
            main_module.knowledge_base.add_qa_pair(
                question=comment_text,
                answer=response,
                source="comment",
                metadata={"comment_id": comment_id, "post_id": post_id}
            )
        else:
            logger.error(f"✗ Failed to send reply to comment {comment_id}")

    except Exception as e:
        logger.error(f"Error handling comment: {e}")

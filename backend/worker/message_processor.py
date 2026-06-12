"""Message processor worker - consumes from queue and processes messages."""

import asyncio
import os
import sys
import signal
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config.settings import settings
from backend.config.logging import get_logger
from backend.integrations.queue_client import queue_client, TOPICS
from backend.worker.ticket_service import ticket_service
from backend.worker.ai_agent import ai_agent
from backend.worker.escalation import escalation_detector
from backend.worker.sentiment import sentiment_analyzer
from backend.db.connection import init_db, close_db
from backend.db.repositories.conversation_repo import conversation_repo
from backend.db.repositories.customer_repo import normalize_phone
from backend.db.repositories.knowledge_repo import knowledge_repo

logger = get_logger(__name__)


class MessageProcessor:
    """Processes messages from the queue."""

    def __init__(self):
        self.running = False
        self.processed_count = 0
        self.error_count = 0

    async def start(self):
        """Start the message processor."""
        logger.info("Starting message processor...")

        # Initialize database
        await init_db(settings.database_url)
        logger.info("Database connected")

        # Start queue consumer
        await queue_client.start_consumer(
            topics=[
                TOPICS["tickets_incoming"],
                TOPICS["escalations"]
            ],
            group_id="fte-message-processor"
        )
        logger.info(f"Consumer started for topics: tickets_incoming, escalations")

        self.running = True

        # Start consuming messages
        await queue_client.consume(self.handle_message)

    async def stop(self):
        """Stop the message processor gracefully."""
        logger.info("Stopping message processor...")
        self.running = False

        # Stop consumer
        await queue_client.stop_consumer()

        # Close database
        await close_db()

        logger.info(
            f"Message processor stopped. "
            f"Processed: {self.processed_count}, Errors: {self.error_count}"
        )

    async def handle_message(self, topic: str, message: Dict[str, Any]):
        """
        Handle incoming message from queue.

        Args:
            topic: Kafka topic name
            message: Message payload
        """
        try:
            logger.info(f"Processing message from {topic}")

            if topic == TOPICS["tickets_incoming"]:
                await self.process_support_request(message)
            elif topic == TOPICS["escalations"]:
                await self.process_escalation(message)
            else:
                logger.warning(f"Unknown topic: {topic}")

            self.processed_count += 1

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            self.error_count += 1

            # Could publish to dead letter queue here
            await self.publish_to_dlq(message, str(e))

    async def _is_message_processed(
        self,
        channel_message_id: str,
        channel: str
    ) -> bool:
        """
        Check if a message has already been processed.

        Args:
            channel_message_id: Unique message ID from channel
            channel: Channel name

        Returns:
            True if already processed, False otherwise
        """
        if not channel_message_id:
            return False

        try:
            async with db.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM processed_messages
                        WHERE channel_message_id = $1 AND channel = $2
                    )
                """, channel_message_id, channel)
                return result
        except Exception as e:
            logger.error(f"Error checking message deduplication: {e}")
            # On error, allow processing to continue (fail open)
            return False

    async def _mark_message_processed(
        self,
        channel_message_id: str,
        channel: str,
        ticket_id: Optional[UUID] = None
    ) -> None:
        """
        Mark a message as processed for deduplication.

        Args:
            channel_message_id: Unique message ID from channel
            channel: Channel name
            ticket_id: Associated ticket ID
        """
        if not channel_message_id:
            return

        try:
            async with db.acquire() as conn:
                await conn.execute("""
                    INSERT INTO processed_messages
                        (channel_message_id, channel, ticket_id)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (channel_message_id) DO NOTHING
                """, channel_message_id, channel, ticket_id)
        except Exception as e:
            logger.error(f"Error marking message as processed: {e}")

    async def process_support_request(self, message: Dict[str, Any]):
        """
        Process incoming support request.

        Flow:
        1. Check for duplicate messages (deduplication)
        2. Extract message data
        3. Check for escalation triggers
        4. Generate AI response
        5. Save response to database
        6. Send response via appropriate channel
        7. Update ticket status

        Args:
            message: Queue message payload
        """
        from backend.db.repositories.customer_repo import customer_repo, normalize_phone
        from backend.db.repositories.conversation_repo import conversation_repo
        from backend.db.repositories.ticket_repo import ticket_repo

        # Step 1: Check for duplicate messages (WhatsApp/Email only)
        channel_message_id = message.get("message_id")
        message_type = message.get("type")

        if channel_message_id and message_type in ("whatsapp_message", "email_message"):
            channel = "whatsapp" if message_type == "whatsapp_message" else "email"

            # Check if already processed
            if await self._is_message_processed(channel_message_id, channel):
                logger.info(f"Duplicate message detected: {channel_message_id} from {channel}. Skipping.")
                return

        # Handle WhatsApp message format
        if message.get("type") == "whatsapp_message":
            from_phone = message.get("from_phone")
            content = message.get("content")
            message_id = message.get("message_id")

            # Find or create customer by phone
            customer = await customer_repo.find_or_create(
                phone=from_phone
            )

            # Check for active conversation
            conversation = await conversation_repo.get_active_by_customer(
                customer_id=customer.id,
                hours=24
            )

            if not conversation:
                conversation = await conversation_repo.create(
                    customer_id=customer.id,
                    initial_channel="whatsapp",
                    metadata={}
                )

                ticket = await ticket_repo.create(
                    conversation_id=conversation.id,
                    customer_id=customer.id,
                    source_channel="whatsapp",
                    category="general"
                )
            else:
                ticket = await ticket_repo.get_by_conversation_id(conversation.id)

            ticket_id = str(ticket.id)
            conversation_id = str(conversation.id)
            customer_id = str(customer.id)
            channel = "whatsapp"
            customer_message = {"content": content}
            customer_info = {"phone": from_phone}

        # Handle Email message format
        elif message.get("type") == "email_message":
            from_email = message.get("from_email")
            content = message.get("content", "")
            subject = message.get("subject", "No Subject")
            message_id = message.get("message_id")

            # Find or create customer by email
            customer = await customer_repo.find_or_create(
                email=from_email
            )

            # Check for active conversation
            conversation = await conversation_repo.get_active_by_customer(
                customer_id=customer.id,
                hours=24
            )

            if not conversation:
                conversation = await conversation_repo.create(
                    customer_id=customer.id,
                    initial_channel="email",
                    metadata={"subject": subject}
                )

                ticket = await ticket_repo.create(
                    conversation_id=conversation.id,
                    customer_id=customer.id,
                    source_channel="email",
                    category="general"
                )
            else:
                ticket = await ticket_repo.get_by_conversation_id(conversation.id)

            ticket_id = str(ticket.id)
            conversation_id = str(conversation.id)
            customer_id = str(customer.id)
            channel = "email"
            customer_message = {"content": content, "subject": subject}
            customer_info = {"email": from_email, "subject": subject}

        else:
            # Web form format
            ticket_id = message.get("ticket_id")
            conversation_id = message.get("conversation_id")
            customer_id = message.get("customer_id")
            channel = message.get("channel", "web_form")
            customer_message = message.get("message", {})
            customer_info = message.get("customer", {})

        logger.info(f"Processing ticket {ticket_id} from {channel}")

        # Initialize response variables (set in escalation or AI branch)
        tokens_used: int = 0
        confidence: float | None = None

        # Step 1: Analyze sentiment
        message_content = customer_message.get("content", "")
        sentiment_result = sentiment_analyzer.analyze(message_content)
        sentiment_score = sentiment_result["score"]

        logger.info(f"Sentiment analysis: score={sentiment_score}, label={sentiment_result['label']}")

        # Step 2: Check for escalation triggers (including sentiment)
        escalation_required, escalation_reason, matched_keywords = escalation_detector.detect_escalation(
            message=message_content,
            sentiment_score=sentiment_score
        )

        if escalation_required:
            logger.info(f"Escalation required for ticket {ticket_id}: {escalation_reason}")

            # Escalate ticket
            await ticket_service.escalate_ticket(
                ticket_id=UUID(ticket_id),
                reason=escalation_reason
            )

            # Send escalation acknowledgment
            response_text = (
                "Thank you for your message. I understand this requires personal attention. "
                "I'm escalating your request to a human agent who will contact you shortly. "
                "Expected response time: Within 1 hour during business hours."
            )

            # Add escalation message to conversation
            await ticket_service.add_message(
                conversation_id=UUID(conversation_id),
                channel=channel,
                direction="outbound",
                role="system",
                content=f"ESCALATION: {escalation_reason}. Matched keywords: {', '.join(matched_keywords)}"
            )

        else:
            # Step 2: Get conversation history
            conversation_history = await self._get_conversation_history(conversation_id)

            # Step 3: Load knowledge base context
            # Try semantic search first, fallback to keyword search
            knowledge_context = await self._load_knowledge_context(message_content)

            # Step 4: Generate AI response
            response_text, tokens_used, confidence = await ai_agent.generate_response(
                message=message_content,
                channel=channel,
                conversation_history=conversation_history,
                knowledge_context=knowledge_context,
                customer_metadata=customer_info
            )

            logger.info(
                f"AI response generated for ticket {ticket_id}: "
                f"{len(response_text)} chars, {tokens_used} tokens"
            )

            # Step 5: Update ticket status to resolved
            await ticket_service.update_ticket_status(
                ticket_id=UUID(ticket_id),
                status="resolved",
                resolution_notes=f"AI resolved with {tokens_used} tokens"
            )

        # Step 6: Save AI response to database
        await ticket_service.add_message(
            conversation_id=UUID(conversation_id),
            channel=channel,
            direction="outbound",
            role="agent",
            content=response_text,
            tokens_used=tokens_used,
            latency_ms=0
        )

        # Step 7: Send response via channel
        if channel == "whatsapp":
            await self.send_whatsapp_response(customer_info, response_text, message.get("message_id"))
        elif channel == "email":
            await self.send_email_response(
                customer_info,
                response_text,
                message.get("subject") or customer_message.get("subject", "Support Request"),
                message.get("message_id"),
                message.get("in_reply_to")
            )

        # Step 8: Mark message as processed for deduplication (WhatsApp/Email only)
        if channel_message_id and message_type in ("whatsapp_message", "email_message"):
            await self._mark_message_processed(
                channel_message_id=channel_message_id,
                channel=channel,
                ticket_id=UUID(ticket_id)
            )

        logger.info(f"Ticket {ticket_id} processing complete")

    async def process_escalation(self, message: Dict[str, Any]):
        """
        Process escalation notification.

        Args:
            message: Queue message payload
        """
        logger.info(f"Processing escalation: {message.get('ticket_id')}")
        # In production, send notification to human agent queue/email

    async def send_whatsapp_response(
        self,
        customer_info: Dict[str, Any],
        response_text: str,
        reply_to_id: Optional[str] = None
    ):
        """
        Send response via WhatsApp.

        Args:
            customer_info: Customer contact information
            response_text: Response to send
            reply_to_id: Message ID to reply to
        """
        from backend.integrations.whatsapp_client import whatsapp_client

        phone = customer_info.get("phone")
        if phone:
            # Normalize phone number
            phone = normalize_phone(phone)

            result = await whatsapp_client.send_text_message(
                to_phone=phone,
                message=response_text,
                reply_to_id=reply_to_id
            )

            if "error" in result:
                logger.error(f"Failed to send WhatsApp message: {result['error']}")
            else:
                logger.info(f"WhatsApp response sent to {phone}")

    async def send_email_response(
        self,
        customer_info: Dict[str, Any],
        response_text: str,
        subject: str,
        message_id: Optional[str] = None,
        in_reply_to: Optional[str] = None
    ):
        """
        Send response via email.

        Args:
            customer_info: Customer contact information
            response_text: Response to send
            subject: Email subject
            message_id: Gmail message ID
            in_reply_to: Message-ID to reply to
        """
        from backend.integrations.email_client import gmail_client

        email = customer_info.get("email") or customer_info.get("from_email")
        if email:
            # Format subject with ticket ID if available
            ticket_id = customer_info.get("ticket_id")
            if ticket_id and not subject.lower().startswith(f"re: ticket"):
                subject = f"Re: Ticket {ticket_id} - {subject}"

            # Send email (use HTML format for better formatting)
            html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto;">
        <p>{response_text.replace(chr(10), '<br>')}</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #666; font-size: 12px;">
            This is an automated response from our AI Support Agent. 
            For further assistance, please reply to this email or visit our support portal.
        </p>
    </div>
</body>
</html>
"""

            # If replying to an email, use send_reply for threading
            if in_reply_to and message_id:
                result = await gmail_client.send_reply(
                    to_email=email,
                    subject=subject,
                    body=html_body,
                    original_message_id=message_id,
                    html=True
                )
            else:
                result = await gmail_client.send_email(
                    to_email=email,
                    subject=subject,
                    body=html_body,
                    html=True
                )

            if "error" in result:
                logger.error(f"Failed to send email: {result['error']}")
            else:
                logger.info(f"Email response sent to {email}")

    async def _get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for context.

        Args:
            conversation_id: Conversation UUID
            limit: Number of messages to retrieve

        Returns:
            List of message dicts with role and content
        """
        try:
            history = await conversation_repo.get_messages(
                conversation_id=UUID(conversation_id),
                limit=limit
            )
            return history
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    async def _load_knowledge_context(
        self,
        query: str,
        limit: int = 3
    ) -> List[Dict[str, str]]:
        """
        Load relevant knowledge base context for a query.

        Tries semantic search first, falls back to keyword search.

        Args:
            query: Customer message/query
            limit: Maximum number of KB entries to load

        Returns:
            List of relevant knowledge base entries
        """
        try:
            # Try semantic search with embeddings
            context = await knowledge_repo.search_similar(
                query=query,
                limit=limit,
                threshold=0.5  # Lower threshold to get more results
            )

            if context:
                logger.info(f"Found {len(context)} KB entries via semantic search")
                return context

            # Fallback: Extract keywords and search
            # Simple keyword extraction (remove common stop words)
            stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                         "being", "have", "has", "had", "do", "does", "did", "will",
                         "would", "could", "should", "may", "might", "must", "shall",
                         "can", "need", "dare", "ought", "used", "to", "of", "in",
                         "for", "on", "with", "at", "by", "from", "as", "into",
                         "through", "during", "before", "after", "and", "but", "or",
                         "nor", "not", "so", "yet", "both", "either", "neither",
                         "each", "every", "all", "any", "few", "more", "most",
                         "other", "some", "such", "no", "only", "own", "same",
                         "than", "too", "very", "s", "t", "just", "don", "now", "i",
                         "me", "my", "myself", "we", "our", "ours", "ourselves",
                         "you", "your", "yours", "yourself", "yourselves",
                         "he", "him", "his", "himself", "she", "her", "hers",
                         "it", "its", "itself", "they", "them", "their", "theirs",
                         "themselves", "what", "which", "who", "whom", "this",
                         "that", "these", "those", "am", "if", "because", "until",
                         "while", "about", "between", "against", "further", "then",
                         "once", "here", "there", "when", "where", "why", "how"}

            words = query.lower().split()
            keywords = [w for w in words if w not in stop_words and len(w) > 3]

            if keywords:
                # Search using first meaningful keyword
                context = await knowledge_repo.search_by_keyword(
                    keyword=keywords[0],
                    limit=limit
                )
                if context:
                    logger.info(f"Found {len(context)} KB entries via keyword search")
                    return context

            # Final fallback: Return empty context
            logger.info("No relevant KB entries found")
            return []

        except Exception as e:
            logger.error(f"Failed to load knowledge base context: {e}")
            return []

    async def publish_to_dlq(self, message: Dict[str, Any], error: str):
        """
        Publish failed message to dead letter queue.

        Args:
            message: Original message
            error: Error message
        """
        dlq_message = {
            "original_message": message,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            await queue_client.publish(
                topic=TOPICS["dlq"],
                message=dlq_message
            )
            logger.info("Message published to DLQ")
        except Exception as e:
            logger.error(f"Failed to publish to DLQ: {e}")


async def main():
    """Main entry point for the worker."""
    processor = MessageProcessor()

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Shutdown signal received")
        asyncio.create_task(processor.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await processor.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await processor.stop()


if __name__ == "__main__":
    asyncio.run(main())

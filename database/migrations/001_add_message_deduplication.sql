-- Migration: Add message deduplication constraint
-- Purpose: Prevent duplicate messages from webhook retries
-- Date: 2026-05-12

-- Add unique constraint on channel_message_id (only for non-NULL values)
-- This prevents duplicate messages from WhatsApp/Email webhooks
CREATE UNIQUE INDEX idx_messages_channel_message_id_unique
ON messages(channel_message_id)
WHERE channel_message_id IS NOT NULL;

-- Add processed_messages table for tracking webhook message IDs
-- This provides an additional layer of deduplication before processing
CREATE TABLE IF NOT EXISTS processed_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_message_id VARCHAR(255) NOT NULL UNIQUE,
    channel VARCHAR(50) NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ticket_id UUID,
    CONSTRAINT chk_processed_channel CHECK (channel IN ('web_form', 'whatsapp', 'email'))
);

-- Index for fast lookups
CREATE INDEX idx_processed_messages_channel_id ON processed_messages(channel, channel_message_id);
CREATE INDEX idx_processed_messages_processed_at ON processed_messages(processed_at);

-- Add TTL cleanup function (optional - keeps table from growing indefinitely)
-- Messages older than 7 days can be cleaned up
COMMENT ON TABLE processed_messages IS 'Tracks processed webhook messages for deduplication. Records older than 7 days can be safely deleted.';

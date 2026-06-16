-- Add per-message feedback columns for inline thumbs up/down
ALTER TABLE messages
ADD COLUMN IF NOT EXISTS feedback VARCHAR(10) DEFAULT NULL
  CHECK (feedback IN ('thumbs_up', 'thumbs_down'));

ALTER TABLE messages
ADD COLUMN IF NOT EXISTS feedback_reason TEXT DEFAULT NULL;

ALTER TABLE messages
ADD COLUMN IF NOT EXISTS feedback_created_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- Remove old ticket-level survey table (data migrated to messages)
DROP TABLE IF EXISTS ticket_surveys;

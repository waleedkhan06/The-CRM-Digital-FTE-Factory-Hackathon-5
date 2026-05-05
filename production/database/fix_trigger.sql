CREATE OR REPLACE FUNCTION update_customer_sentiment()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customers 
    SET avg_sentiment = (
        SELECT COALESCE(AVG(m.sentiment_score), 0.50)
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.customer_id = NEW.customer_id
    ),
    total_interactions = (
        SELECT COUNT(DISTINCT c.id)
        FROM conversations c
        WHERE c.customer_id = NEW.customer_id
    ),
    updated_at = NOW()
    WHERE id = NEW.customer_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

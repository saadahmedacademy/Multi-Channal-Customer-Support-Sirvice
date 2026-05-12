"""Customer identifier repository for cross-channel recognition."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from backend.db.connection import db
import logging

logger = logging.getLogger(__name__)


class CustomerIdentifierRepository:
    """Repository for customer identifier operations."""

    async def add_identifier(
        self,
        customer_id: UUID,
        identifier_type: str,
        identifier_value: str,
        verified: bool = False
    ) -> bool:
        """
        Add an identifier to a customer.

        Args:
            customer_id: Customer UUID
            identifier_type: Type ('email', 'phone', 'whatsapp')
            identifier_value: The identifier value
            verified: Whether this identifier is verified

        Returns:
            True if successful
        """
        try:
            async with db.acquire() as conn:
                await conn.execute("""
                    INSERT INTO customer_identifiers
                        (customer_id, identifier_type, identifier_value, verified)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (identifier_type, identifier_value) DO NOTHING
                """, customer_id, identifier_type, identifier_value, verified)
            
            logger.info(f"Added {identifier_type} identifier for customer {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add identifier: {e}")
            return False

    async def get_customer_by_identifier(
        self,
        identifier_type: str,
        identifier_value: str
    ) -> Optional[UUID]:
        """
        Find customer by identifier.

        Args:
            identifier_type: Type ('email', 'phone', 'whatsapp')
            identifier_value: The identifier value

        Returns:
            Customer UUID if found
        """
        try:
            async with db.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT customer_id
                    FROM customer_identifiers
                    WHERE identifier_type = $1
                      AND identifier_value = $2
                """, identifier_type, identifier_value)
                
                return row["customer_id"] if row else None
                
        except Exception as e:
            logger.error(f"Failed to lookup identifier: {e}")
            return None

    async def get_all_identifiers(
        self,
        customer_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all identifiers for a customer.

        Args:
            customer_id: Customer UUID

        Returns:
            List of identifier dicts
        """
        try:
            async with db.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT identifier_type, identifier_value, verified, created_at
                    FROM customer_identifiers
                    WHERE customer_id = $1
                    ORDER BY created_at DESC
                """, customer_id)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get identifiers: {e}")
            return []

    async def verify_identifier(
        self,
        customer_id: UUID,
        identifier_type: str,
        identifier_value: str
    ) -> bool:
        """
        Mark an identifier as verified.

        Args:
            customer_id: Customer UUID
            identifier_type: Type
            identifier_value: Value

        Returns:
            True if successful
        """
        try:
            async with db.acquire() as conn:
                await conn.execute("""
                    UPDATE customer_identifiers
                    SET verified = TRUE
                    WHERE customer_id = $1
                      AND identifier_type = $2
                      AND identifier_value = $3
                """, customer_id, identifier_type, identifier_value)
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to verify identifier: {e}")
            return False

    async def link_identifiers(
        self,
        customer_id: UUID,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> None:
        """
        Link multiple identifiers to a customer.

        Args:
            customer_id: Customer UUID
            email: Email address to link
            phone: Phone number to link
        """
        if email:
            await self.add_identifier(
                customer_id=customer_id,
                identifier_type="email",
                identifier_value=email.lower().strip(),
                verified=False
            )
        
        if phone:
            await self.add_identifier(
                customer_id=customer_id,
                identifier_type="phone",
                identifier_value=phone,
                verified=False
            )


# Global repository instance
customer_identifier_repo = CustomerIdentifierRepository()

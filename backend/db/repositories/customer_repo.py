"""Customer repository for database operations."""

from typing import Optional, List, Dict, Any
from uuid import UUID
import asyncpg
import re
import json
from backend.db.models.customer import Customer
from backend.db.connection import db


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to E.164 format.
    
    Args:
        phone: Phone number string
        
    Returns:
        Phone number in E.164 format (e.g., +14155551234)
    """
    if not phone:
        return phone
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Ensure it starts with +
    if not cleaned.startswith('+'):
        # Assume US numbers if no country code
        if len(cleaned) == 10:
            cleaned = '+1' + cleaned
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            cleaned = '+' + cleaned
        else:
            # Try to detect country code
            cleaned = '+' + cleaned
    
    return cleaned


class CustomerRepository:
    """Repository for customer database operations."""
    
    async def create(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Customer:
        """
        Create a new customer.
        
        Args:
            email: Customer email address
            phone: Customer phone number (E.164 format)
            name: Customer display name
            metadata: Additional customer attributes
            
        Returns:
            Created Customer instance
        """
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO customers (email, phone, name, metadata)
                VALUES ($1, $2, $3, $4)
                RETURNING id, email, phone, name, created_at, metadata
            """, email, phone, name, json.dumps(metadata or {}))

            return Customer.from_row(row)
    
    async def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Get a customer by ID."""
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, email, phone, name, created_at, metadata
                FROM customers
                WHERE id = $1
            """, customer_id)
            
            return Customer.from_row(row) if row else None
    
    async def get_by_email(self, email: str) -> Optional[Customer]:
        """Get a customer by email address."""
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, email, phone, name, created_at, metadata
                FROM customers
                WHERE email = LOWER(TRIM($1))
            """, email)
            
            return Customer.from_row(row) if row else None
    
    async def get_by_phone(self, phone: str) -> Optional[Customer]:
        """Get a customer by phone number."""
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, email, phone, name, created_at, metadata
                FROM customers
                WHERE phone = $1
            """, phone)
            
            return Customer.from_row(row) if row else None
    
    async def find_or_create(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None
    ) -> Customer:
        """
        Find existing customer by email or phone, or create new one.

        Args:
            email: Customer email address
            phone: Customer phone number
            name: Customer display name

        Returns:
            Existing or newly created Customer
        """
        # Normalize phone if provided
        if phone:
            phone = normalize_phone(phone)
        
        # Try to find by email
        if email:
            customer = await self.get_by_email(email)
            if customer:
                return customer

        # Try to find by phone
        if phone:
            customer = await self.get_by_phone(phone)
            if customer:
                return customer

        # Create new customer
        return await self.create(email=email, phone=phone, name=name)
    
    async def update(
        self,
        customer_id: UUID,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Customer]:
        """
        Update customer information.
        
        Args:
            customer_id: Customer ID to update
            email: New email address
            phone: New phone number
            name: New display name
            metadata: New metadata (merged with existing)
            
        Returns:
            Updated Customer instance or None if not found
        """
        async with db.acquire() as conn:
            # Get existing customer
            existing = await self.get_by_id(customer_id)
            if not existing:
                return None
            
            # Merge metadata if provided
            if metadata and existing.metadata:
                metadata = {**existing.metadata, **metadata}
            
            row = await conn.fetchrow("""
                UPDATE customers
                SET email = COALESCE($1, email),
                    phone = COALESCE($2, phone),
                    name = COALESCE($3, name),
                    metadata = COALESCE($4, metadata)
                WHERE id = $5
                RETURNING id, email, phone, name, created_at, metadata
            """, email, phone, name, metadata, customer_id)
            
            return Customer.from_row(row) if row else None


# Global repository instance
customer_repo = CustomerRepository()

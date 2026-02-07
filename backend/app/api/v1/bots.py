from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.bot import Bot
from app.schemas.bot import (
    BotCreate,
    BotUpdate,
    BotHeartbeat,
    BotResponse,
    BotListResponse,
    BotFilterParams
)
from app.core.deps import get_current_user_id_optional, get_current_user_id

router = APIRouter(prefix="/bots", tags=["bots"])


@router.post("/register", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
def register_bot(
    bot_data: BotCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
) -> Bot:
    """
    Register a new bot.

    - **bot_id**: Unique identifier for the bot
    - **bot_name**: Display name of the bot
    - **owner_id**: UUID of the bot owner
    - **description**: Optional bot description
    - **capabilities**: JSON object describing bot capabilities
    - **endpoint**: Optional bot endpoint URL
    - **version**: Optional bot version
    """
    # Check if bot_id already exists
    existing_bot = db.query(Bot).filter(Bot.bot_id == bot_data.bot_id).first()
    if existing_bot:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bot with bot_id '{bot_data.bot_id}' already exists"
        )

    # Create new bot
    db_bot = Bot(
        bot_id=bot_data.bot_id,
        bot_name=bot_data.bot_name,
        owner_id=bot_data.owner_id,
        description=bot_data.description,
        capabilities=bot_data.capabilities,
        endpoint=bot_data.endpoint,
        version=bot_data.version,
        status="offline"
    )

    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)

    return db_bot


@router.post("/{bot_id}/heartbeat", response_model=BotResponse)
def bot_heartbeat(
    bot_id: str,
    heartbeat: BotHeartbeat,
    db: Session = Depends(get_db)
) -> Bot:
    """
    Report bot heartbeat.

    Updates the bot's status and last heartbeat timestamp.
    """
    db_bot = db.query(Bot).filter(Bot.bot_id == bot_id).first()

    if not db_bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with bot_id '{bot_id}' not found"
        )

    # Update bot status and heartbeat
    db_bot.status = heartbeat.status
    db_bot.last_heartbeat_at = datetime.utcnow()

    if heartbeat.capabilities is not None:
        db_bot.capabilities = heartbeat.capabilities

    if heartbeat.version is not None:
        db_bot.version = heartbeat.version

    db.commit()
    db.refresh(db_bot)

    return db_bot


@router.get("", response_model=BotListResponse)
def list_bots(
    status: Optional[str] = Query(None, description="Filter by status"),
    owner_id: Optional[UUID] = Query(None, description="Filter by owner"),
    search: Optional[str] = Query(None, description="Search in bot_name and description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
) -> dict:
    """
    Get list of bots with pagination and filtering.

    - **status**: Filter by bot status (online, offline, busy, error)
    - **owner_id**: Filter by owner UUID
    - **search**: Search in bot_name and description
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    """
    query = db.query(Bot)

    # Apply filters
    if status:
        query = query.filter(Bot.status == status)

    if owner_id:
        query = query.filter(Bot.owner_id == owner_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Bot.bot_name.ilike(search_pattern)) |
            (Bot.description.ilike(search_pattern))
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    bots = query.offset(offset).limit(page_size).all()

    # Calculate pages
    pages = (total + page_size - 1) // page_size

    return {
        "items": bots,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.get("/{bot_id}", response_model=BotResponse)
def get_bot(
    bot_id: str,
    db: Session = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
) -> Bot:
    """
    Get bot details by bot_id.
    """
    db_bot = db.query(Bot).filter(Bot.bot_id == bot_id).first()

    if not db_bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with bot_id '{bot_id}' not found"
        )

    return db_bot


@router.patch("/{bot_id}", response_model=BotResponse)
def update_bot(
    bot_id: str,
    bot_update: BotUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
) -> Bot:
    """
    Update bot information.
    """
    db_bot = db.query(Bot).filter(Bot.bot_id == bot_id).first()

    if not db_bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with bot_id '{bot_id}' not found"
        )

    # Update fields
    update_data = bot_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_bot, field, value)

    db_bot.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_bot)

    return db_bot


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bot(
    bot_id: str,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
) -> None:
    """
    Delete a bot.
    """
    db_bot = db.query(Bot).filter(Bot.bot_id == bot_id).first()

    if not db_bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot with bot_id '{bot_id}' not found"
        )

    db.delete(db_bot)
    db.commit()

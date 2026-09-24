"""Note management action."""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import or_

from app.actions.base import BaseAction
from app.db.models import Note


class NoteAction(BaseAction):
    """Create and manage quick notes."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the note action with a database session."""
        self.session = session

    @property
    def name(self) -> str:
        return "notes"

    @property
    def description(self) -> str:
        return "Create and manage quick notes"

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the action with given parameters."""
        action = params.get("action")
        if not action:
            return {"success": False, "message": "Missing 'action' parameter."}

        try:
            if action == "create_note":
                return await self._create_note(params)
            elif action == "list_notes":
                return await self._list_notes(params)
            elif action == "search_notes":
                return await self._search_notes(params)
            elif action == "delete_note":
                return await self._delete_note(params)
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "message": f"Error executing note action: {e}"}

    async def _create_note(self, params: dict[str, Any]) -> dict[str, Any]:
        title = params.get("title")
        content = params.get("content", "")
        tags = params.get("tags", "")

        if not title:
            return {"success": False, "message": "Title is required to create a note."}

        note = Note(
            title=title,
            content=content,
            tags=tags
        )
        self.session.add(note)
        await self.session.commit()
        
        return {
            "success": True,
            "message": "Note created successfully.",
            "note_id": note.id
        }

    async def _list_notes(self, params: dict[str, Any]) -> dict[str, Any]:
        tag = params.get("tag")
        stmt = select(Note)
        if tag:
            stmt = stmt.where(Note.tags.ilike(f"%{tag}%"))
        
        result = await self.session.execute(stmt)
        notes = result.scalars().all()
        
        notes_data = [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "tags": n.tags
            }
            for n in notes
        ]
        return {"success": True, "message": f"Found {len(notes)} notes.", "notes": notes_data}
        
    async def _search_notes(self, params: dict[str, Any]) -> dict[str, Any]:
        keyword = params.get("keyword")
        if not keyword:
            return {"success": False, "message": "keyword is required for searching."}

        stmt = select(Note).where(
            or_(
                Note.title.ilike(f"%{keyword}%"),
                Note.content.ilike(f"%{keyword}%")
            )
        )
        result = await self.session.execute(stmt)
        notes = result.scalars().all()
        
        notes_data = [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "tags": n.tags
            }
            for n in notes
        ]
        return {"success": True, "message": f"Found {len(notes)} matching notes.", "notes": notes_data}

    async def _delete_note(self, params: dict[str, Any]) -> dict[str, Any]:
        note_id = params.get("note_id")
        if not note_id:
            return {"success": False, "message": "note_id is required."}

        stmt = select(Note).where(Note.id == note_id)
        result = await self.session.execute(stmt)
        note = result.scalar_one_or_none()

        if not note:
            return {"success": False, "message": f"Note {note_id} not found."}

        await self.session.delete(note)
        await self.session.commit()
        return {"success": True, "message": f"Note {note_id} deleted successfully."}

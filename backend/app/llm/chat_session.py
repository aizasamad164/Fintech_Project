# backend/app/llm/chat_session.py
from typing import List, Dict, Any, Optional

# Global in-memory storage fallback for local testing without Supabase
_IN_MEMORY_HISTORY: Dict[str, List[Dict[str, Any]]] = {}

try:
    from app.lib.supabaseClient import supabase
    SUPABASE_AVAILABLE = supabase is not None
except Exception:
    SUPABASE_AVAILABLE = False


class ChatSessionManager:
    """
    Manages chat history persistence with automatic in-memory fallback
    if Supabase is not connected.
    """

    @staticmethod
    async def get_history(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        if SUPABASE_AVAILABLE:
            try:
                res = supabase.table("chat_history")\
                    .select("role, content")\
                    .eq("session_id", session_id)\
                    .order("created_at", desc=False)\
                    .limit(limit)\
                    .execute()
                if res.data:
                    return res.data
            except Exception as e:
                print(f"[ChatSessionManager] Supabase offline/unreachable ({e}). Using in-memory history.")

        # Fallback to local memory
        history = _IN_MEMORY_HISTORY.get(session_id, [])
        return history[-limit:]

    @staticmethod
    async def save_message(session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        # 1. Update in-memory history
        if session_id not in _IN_MEMORY_HISTORY:
            _IN_MEMORY_HISTORY[session_id] = []
        
        _IN_MEMORY_HISTORY[session_id].append({"role": role, "content": content})

        # 2. Persist to Supabase if available
        if SUPABASE_AVAILABLE:
            try:
                payload = {"session_id": session_id, "role": role, "content": content}
                if metadata:
                    payload["metadata"] = metadata
                supabase.table("chat_history").insert(payload).execute()
            except Exception as e:
                print(f"[ChatSessionManager] Supabase save bypassed: {e}")
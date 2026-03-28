from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from config import get_settings


class SimpleStorage:
    """Minimal storage for Supabase Auth to avoid NoneType errors."""
    def __init__(self):
        self.items = {}

    def get_item(self, key: str):
        return self.items.get(key)

    def set_item(self, key: str, value: str):
        self.items[key] = value

    def remove_item(self, key: str):
        self.items.pop(key, None)


def get_supabase() -> Client:
    """Get regular Supabase client with anon key for user-specific operations (login, etc.)."""
    settings = get_settings()
    options = ClientOptions(storage=SimpleStorage())
    client = create_client(settings.supabase_url, settings.supabase_key, options=options)
    
    # Fix for library bug where realtime is None but accessed in auth events
    if getattr(client, "realtime", None) is None:
        class FakeRealtime:
            def set_auth(self, token): pass
        client.realtime = FakeRealtime()
        
    return client


def get_admin_client() -> Client:
    """Get Supabase client with service role key for admin operations (registration, etc.)."""
    settings = get_settings()
    options = ClientOptions(storage=SimpleStorage())
    client = create_client(settings.supabase_url, settings.supabase_service_key, options=options)
    
    if getattr(client, "realtime", None) is None:
        class FakeRealtime:
            def set_auth(self, token): pass
        client.realtime = FakeRealtime()
        
    return client

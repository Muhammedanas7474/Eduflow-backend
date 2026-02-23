import os
import sys

import django
from django.db import connection

# Setup Django environment
sys.path.append("/Users/m1/Desktop/BackeUp/Eduflow-backend/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduflow.settings")
django.setup()


def drop_chat_tables():
    with connection.cursor() as cursor:
        tables = [
            "chat_callsession",
            "chat_chatmessage",
            "chat_chatroommember",
            "chat_chatroom",
        ]
        for table in tables:
            try:
                print(f"Dropping table {table}...")
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"Dropped {table}")
            except Exception as e:
                print(f"Error dropping {table}: {e}")


if __name__ == "__main__":
    drop_chat_tables()

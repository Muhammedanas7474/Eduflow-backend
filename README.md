# Eduflow
```text
eduflow-project/
├── venv/                     ← virtual environment (DO NOT touch)
│   ├── bin/
│   ├── lib/
│   └── pyvenv.cfg
│
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env
│   │
│   ├── eduflow/
│   │   ├── __init__.py
│   │   ├── settings.py       ← single settings file (correct)
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── apps/
│   │   ├── accounts/
│   │   │   ├── migrations/
│   │   │   │   └── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── apps.py
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py   ← may be empty (OK)
│   │   │   └── urls.py
│   │   │
│   │   ├── tenants/
│   │   │   ├── migrations/
│   │   │   │   └── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── apps.py
│   │   │   └── models.py
│   │   │
│   │   └── common/
│   │       ├── __init__.py
│   │       ├── admin.py
│   │       ├── apps.py
│   │       ├── responses.py
│   │       └── exceptions.py
│   │
│   └── db.sqlite3   ← may exist (OK even if using Postgres)
│
├── .gitignore
└── README.md

# FastAPI WebSocket Chat

A real-time chat backend built with **FastAPI**, **WebSockets**, and **PostgreSQL**. Supports JWT-authenticated connections, broadcast and private messaging, live online-presence tracking, and paginated chat history — plus a minimal HTML client for manual testing.

## Features

- **JWT authentication** — register/login over REST, then connect to the WebSocket using the issued token
- **Real-time messaging** over a single `/ws` WebSocket endpoint, with:
  - Broadcast (`chat`) and 1:1 (`private_chat`) message types
  - Multi-tab/multi-device support per user (a user can have several active connections; presence only flips offline once *all* connections close)
- **Online presence** — new connections receive a `presence_sync` snapshot of who's online, and presence changes are broadcast to everyone else
- **Persistent chat history** — private messages are saved to PostgreSQL and retrievable via cursor-based pagination (`before_id` / `limit`, capped at 100)
- **Offline delivery handling** — private messages are still persisted even if the receiver isn't connected; the sender gets an explicit error if the receiver is offline or doesn't exist
- **Database migrations** via Alembic (`users` and `messages` tables)
- **Test client** (`frontend/test.html`) — a dependency-free HTML/JS page for logging in, sending messages, and browsing history against a running backend

## Tech Stack

- **FastAPI** + **Starlette** (WebSocket support), **Uvicorn**
- **PostgreSQL** via **SQLAlchemy 2.0** (ORM) + **Alembic** (migrations) + `psycopg2-binary`
- **PyJWT** for token issuance/verification, **pwdlib** for password hashing
- **Pydantic** for request/event schema validation

## Project Structure

```
fastapi-websocket-chat/
├── backend/
│   ├── alembic/
│   │   ├── versions/          # migration scripts
│   │   └── env.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── app/
│       ├── main.py            # FastAPI app + router registration
│       ├── api/
│       │   ├── auth.py        # /auth/register, /auth/login
│       │   ├── websocket.py   # /ws endpoint and event routing
│       │   ├── database.py    # /database/test connectivity check
│       │   └── health.py      # /health
│       ├── core/
│       │   ├── config.py      # settings loaded from .env
│       │   └── security.py    # JWT + password hashing
│       ├── db/
│       │   ├── database.py    # engine/session setup
│       │   └── models.py      # User, Message ORM models
│       ├── schemas/
│       │   └── events.py      # WebSocket event payload schemas
│       └── services/
│           ├── chat_service.py         # message persistence & history queries
│           └── connection_manager.py   # in-memory connection/presence registry
└── frontend/
    └── test.html           # manual WebSocket test client
```

## How It Works

### Authentication

1. `POST /auth/register` — creates a user with a hashed password (`pwdlib`).
2. `POST /auth/login` — verifies credentials and returns a JWT (`{"sub": username, "exp": ...}`), signed with `SECRET_KEY`/`ALGORITHM` from settings.
3. The client connects to the WebSocket as `ws://<host>/ws?token=<jwt>`. The server decodes and validates the token before accepting the connection; an invalid or missing token closes the socket with code `1008`.

### WebSocket Event Protocol

All messages over `/ws` are JSON with a `type` field:

| Type | Direction | Payload | Behavior |
|---|---|---|---|
| `presence_sync` | server → client | `users: [string]` | Sent once on connect with the current online user list |
| `presence` | server → client | `username, status` | Broadcast when a user's first/last connection comes online or goes fully offline |
| `chat` | client ↔ server | `message` | Broadcast to all connected clients |
| `private_chat` | client ↔ server | `receiver, message` | Persisted to the database, then delivered only if the receiver is currently online; sender gets an `error` event otherwise |
| `get_chat_history` | client → server | `receiver, before_id?, limit?` | Returns a `chat_history` event with a chronological page of messages between the two users, plus `has_more`/`oldest_id` for cursor pagination |
| `error` | server → client | `message` | Sent for unknown event types or delivery failures |

### Connection Manager

`ConnectionManager` (in `services/connection_manager.py`) keeps an in-memory `dict[username, set[WebSocket]]`. This supports multiple simultaneous connections per user (e.g. several browser tabs) while only firing presence-offline events once every connection for that user has dropped.

### Persistence

`chat_service.py` handles saving private messages and fetching paginated history using a "fetch one extra row" trick to cheaply compute `has_more` without a separate count query. History is always returned in chronological order regardless of the descending query used internally.

## Getting Started

### Prerequisites

- Python 3.11+
- A running PostgreSQL instance

### Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` with:

```
APP_NAME=FastAPI WebSocket Chat
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql://user:password@localhost:5432/chat_db
```

Run database migrations:

```bash
alembic upgrade head
```

Start the server:

```bash
uvicorn app.main:app --reload
```

The API is now available at `http://127.0.0.1:8000`, with interactive docs at `/docs`.

### Trying It Out

1. Open `frontend/test.html` directly in a browser (no build step needed).
2. Register two users via the API (or extend the test page to call `/auth/register`), then log in as each in separate browser tabs/profiles.
3. Use the page to broadcast messages, send private messages, and load chat history between two users.

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/database/test` | Verifies the database connection |
| `POST` | `/auth/register` | Create a new user |
| `POST` | `/auth/login` | Authenticate and receive a JWT |
| `WS` | `/ws?token=<jwt>` | Real-time chat connection |

## Notes / Current Limitations

- CORS is currently wide open (`allow_origins=["*"]`) — tighten this before any real deployment.
- The connection registry is in-memory and per-process, so it won't scale horizontally without an external pub/sub layer (e.g. Redis) to share presence and message delivery across multiple server instances.
- `frontend/test.html` is a manual test harness rather than a production frontend.

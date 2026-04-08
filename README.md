# Web Support Form — Next.js Application

> **This folder will contain the Next.js Web Support Form component.**

## Setup Instructions

Run this command in this directory to install Next.js:

```bash
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --import-alias "@/*"
```

Or if you prefer a manual setup:

```bash
npm init -y
npm install next react react-dom
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

## What Will Be Built

Once Next.js is installed, the following files will be created:

| File | Purpose |
|------|---------|
| `components/SupportForm.tsx` | Main React form component |
| `components/TicketStatus.tsx` | Ticket status checker component |
| `app/page.tsx` | Main page with support form |
| `app/ticket/[id]/page.tsx` | Ticket status page |
| `app/api/support/route.ts` | API proxy (optional) |

## API Endpoints Used

The form communicates with the FastAPI backend at:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/support/submit` | POST | Submit support form |
| `/support/ticket/{id}` | GET | Check ticket status |
| `/health` | GET | Health check |

**Default API URL:** `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_URL` env var)

## Wait for Instructions

**Do not build the form yet.** The Phase 2 backend components are being built first.
Once all backend components are complete, the Web Support Form UI will be implemented here.

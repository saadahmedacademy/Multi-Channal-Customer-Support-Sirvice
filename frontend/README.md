# AI Support Center — Frontend

Next.js 16 frontend for the multi-channel AI customer support system. [Live on Vercel](https://multi-channal-customer-support-sirv.vercel.app).

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **Deployment**: Vercel (auto-deploy from `main`)

## Pages

| Route | Description |
|-------|-------------|
| `/` | Main page — contact form + ticket status check |
| `/ticket/[id]` | Direct ticket status lookup |
| `/customers/link` | Link customer identifiers across channels |
| `/privacy` | Privacy Policy |
| `/terms` | Terms of Service |

## API Routes (Next.js)

| Route | Description |
|-------|-------------|
| `POST /api/submit` | Forward support form to backend |
| `GET /api/ticket/[ticketId]` | Fetch ticket status from backend |
| `POST /api/customers/link-identifiers` | Link customer identifiers |
| `GET /api/health` | Health check for Docker HEALTHCHECK |

## Environment

```env
BACKEND_URL=http://localhost:8000   # Backend API base URL
```

## Development

```bash
npm install
npm run dev      # http://localhost:3000
npm run build    # Production build
npm run lint     # Lint check
```

## Conventions

- Components in `src/components/`
- Shared utilities in `src/lib/`
- Tailwind classes only (no CSS modules)
- Glassmorphism card style (`backdrop-blur-md bg-white/60 ... rounded-2xl`)
- Dark mode via `dark:` variant + localStorage theme persistence

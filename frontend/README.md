# AgentKit Frontend

Modern NextJS frontend for the AgentKit multi-agent AI assistant, featuring real-time agent communication via AG-UI protocol.

## Features

- ✅ **Chat Interface**: Clean, intuitive chat UI with Shadcn UI components
- ✅ **Thread Management**: Create, view, and delete chat threads
- ✅ **Real-time Streaming**: AG-UI protocol for streaming agent responses
- ✅ **LocalStorage Persistence**: Client-side thread and message storage
- ✅ **Responsive Design**: Mobile-friendly layout with Tailwind CSS
- ✅ **TypeScript**: Full type safety throughout the application
- ✅ **Dark Mode Support**: Automatic dark mode via Shadcn UI

## Tech Stack

- **NextJS 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Shadcn UI** - Beautiful, accessible UI components
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Icon library
- **AG-UI Protocol** - Real-time agent communication

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL
```

### Development

```bash
# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
# Create production build
npm run build

# Start production server
npm start
```

## Environment Variables

Create a `.env.local` file:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Documentation

Comprehensive documentation available in `/.docs/2-knowledge-base/frontend/`:

- [Architecture Overview](../.docs/2-knowledge-base/frontend/README.md)
- [Components Guide](../.docs/2-knowledge-base/frontend/components.md)
- [Hooks Guide](../.docs/2-knowledge-base/frontend/hooks.md)
- [Services Guide](../.docs/2-knowledge-base/frontend/services.md)
- [AG-UI Integration](../.docs/2-knowledge-base/frontend/agui-integration.md)
- [Backend Integration](../.docs/2-knowledge-base/frontend/backend-integration.md)

## License

MIT

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

# Claude Agent Frontend

Next.js-based web application for the Claude Agent system.

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

## Architecture

- Built with Next.js 14 and React 18
- TypeScript for type safety
- Deployed as static site to S3/CloudFront
- Uses shared types from `@claude-agent/shared`

## Environment Variables

Copy `.env.example` to `.env.local` and configure:

- `NEXT_PUBLIC_API_URL`: Backend API endpoint
- `NEXT_PUBLIC_AWS_REGION`: AWS region for client-side SDK
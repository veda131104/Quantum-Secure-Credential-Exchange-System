# DigiLocker 2.0 Frontend

Next.js frontend for DigiLocker 2.0 - Quantum-Secure Digital Credential Locker

## Getting Started

### Install Dependencies

```bash
npm install
```

### Configure Environment

Create `.env.local` file:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your backend URL.

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Features

- User registration and authentication
- Biometric login (face recognition)
- Credential wallet
- Share credentials with time-bound links
- Verify credentials
- Issuer portal
- Admin dashboard

## Tech Stack

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Axios for API calls
- Ethers.js for blockchain interaction

## Project Structure

```
src/
├── pages/           # Next.js pages
├── components/      # React components
├── lib/             # Utilities (API client, helpers)
└── styles/          # Global styles
```

## Pages

- `/` - Landing page
- `/login` - User login
- `/register` - User registration
- `/dashboard` - User dashboard (TODO)
- `/wallet` - Credential wallet (TODO)
- `/issuer` - Issuer portal (TODO)
- `/verify` - Credential verification (TODO)
- `/admin` - Admin dashboard (TODO)

## Development Notes

Most pages are TODO and need to be implemented. The landing page and API client are ready.

Implement remaining pages based on the API endpoints available in the backend.

# Frontend Documentation

## Setup & Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
# Access at http://localhost:5173

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Fix linting issues
npm run lint:fix
```

## Project Structure

```
frontend/
├── src/
│   ├── components/         # Reusable components (Header, Footer, Layout)
│   ├── pages/             # Page components (LoginPage, JobsPage, etc.)
│   ├── lib/
│   │   ├── api.js         # Axios API client with interceptors
│   │   └── store.js       # Zustand stores (auth, jobs, CVs)
│   ├── App.jsx            # Main app component with routing
│   ├── main.jsx           # React entry point
│   └── index.css          # Global styles (Tailwind)
├── index.html             # HTML template
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── eslint.config.js
├── Dockerfile
└── .dockerignore
```

## Features

### Pages
- **HomePage**: Featured jobs and overview
- **JobsPage**: Job search with filters
- **JobDetailPage**: Job details and apply button
- **LoginPage**: User authentication
- **RegisterPage**: New user registration
- **DashboardPage**: User dashboard with stats
- **ProfilePage**: User profile management

### Components
- **Layout**: Main layout wrapper with Header & Footer
- **Header**: Navigation and user menu
- **Footer**: Footer with links

### State Management
- **useAuthStore**: User authentication state
- **useJobStore**: Jobs and search filters
- **useCVStore**: User CV management

## API Integration

All API calls use `apiClient` from `lib/api.js`:
- Automatic Bearer token injection
- Global error handling (401 redirects to login)
- Base URL from `VITE_API_URL` env var

## Styling

- **Tailwind CSS** for utility-first styling
- **Lucide React** for icons
- Responsive design with mobile-first approach
- Custom theme colors in `tailwind.config.js`

## Environment Variables

```env
VITE_API_URL=http://localhost/api/v1
```

## Docker

```bash
# Build image
docker build -t job-matching-frontend .

# Run container
docker run -p 3000:3000 job-matching-frontend
```

## Performance Optimization

- Code splitting with React Router
- Lazy loading with React.lazy()
- Image optimization
- Gzip compression in build

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Future Enhancements

- [ ] Add CV upload functionality
- [ ] Add job recommendations
- [ ] Add saved jobs feature
- [ ] Add user notifications
- [ ] Add dark mode
- [ ] Improve accessibility (a11y)

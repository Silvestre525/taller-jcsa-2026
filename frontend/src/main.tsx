import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createRootRoute, createRoute, createRouter, RouterProvider } from '@tanstack/react-router'
import { AuthProvider } from './auth'
import { Home, Layout, Tasks } from './pages'
import './styles.css'

const rootRoute = createRootRoute({ component: Layout })
const indexRoute = createRoute({ getParentRoute: () => rootRoute, path: '/', component: Home })
const tasksRoute = createRoute({ getParentRoute: () => rootRoute, path: '/tareas', component: Tasks })
const router = createRouter({ routeTree: rootRoute.addChildren([indexRoute, tasksRoute]) })

declare module '@tanstack/react-router' {
  interface Register { router: typeof router }
}

const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </AuthProvider>
  </StrictMode>,
)

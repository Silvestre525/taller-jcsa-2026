import {
  ClerkProvider, SignedIn, SignedOut, SignInButton, UserButton, useAuth,
} from '@clerk/clerk-react'
import type { ReactNode } from 'react'

const KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined
// Sin clave de Clerk => modo demo. Es constante en tiempo de build, por eso los hooks son estables.
export const DEMO = !KEY

export function AuthProvider({ children }: { children: ReactNode }) {
  if (DEMO) return <>{children}</>
  return <ClerkProvider publishableKey={KEY!} afterSignOutUrl="/">{children}</ClerkProvider>
}

export function useToken(): () => Promise<string | null> {
  if (DEMO) return async () => 'demo'
  return useAuth().getToken
}

export function Gate({ children }: { children: ReactNode }) {
  if (DEMO) return <>{children}</>
  return (
    <>
      <SignedIn>{children}</SignedIn>
      <SignedOut>
        <p>Iniciá sesión para ver tus tareas.</p>
        <SignInButton mode="modal"><button className="btn">Iniciar sesión</button></SignInButton>
      </SignedOut>
    </>
  )
}

export function UserMenu() {
  if (DEMO) return <span className="badge">sin login</span>
  return (
    <>
      <SignedOut><SignInButton mode="modal"><button className="btn">Ingresar</button></SignInButton></SignedOut>
      <SignedIn><UserButton /></SignedIn>
    </>
  )
}

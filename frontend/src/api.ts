export type Task = { id: number; title: string; done: boolean; created_at: string }

export type Api = {
  list: () => Promise<Task[]>
  create: (title: string) => Promise<Task>
  toggle: (id: number) => Promise<Task>
  remove: (id: number) => Promise<void>
  welcome: (email: string) => Promise<{ sent: boolean }>
}

const API = import.meta.env.VITE_API_URL as string | undefined

// API falsa en memoria para ver la interfaz sin backend.
let seq = 3
let store: Task[] = [
  { id: 2, title: 'Crear cuenta en Neon', done: true, created_at: new Date().toISOString() },
  { id: 1, title: 'Desplegar el front en Cloudflare Pages', done: false, created_at: new Date().toISOString() },
]
const wait = <T,>(v: T) => new Promise<T>((r) => setTimeout(() => r(v), 250))
const mockApi: Api = {
  list: () => wait([...store]),
  create: async (title) => {
    const t = { id: seq++, title, done: false, created_at: new Date().toISOString() }
    store = [t, ...store]
    return wait(t)
  },
  toggle: async (id) => {
    store = store.map((t) => (t.id === id ? { ...t, done: !t.done } : t))
    return wait(store.find((t) => t.id === id)!)
  },
  remove: async (id) => {
    store = store.filter((t) => t.id !== id)
    return wait(undefined)
  },
  welcome: () => wait({ sent: true }),
}

export function createApi(getToken: () => Promise<string | null>): Api {
  if (!API) return mockApi
  const call = async <T,>(path: string, init: RequestInit = {}): Promise<T> => {
    const token = await getToken()
    const res = await fetch(`${API}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...init.headers },
    })
    if (!res.ok) throw new Error(`Error ${res.status}`)
    return (res.status === 204 ? undefined : await res.json()) as T
  }
  return {
    list: () => call<Task[]>('/api/tasks'),
    create: (title) => call<Task>('/api/tasks', { method: 'POST', body: JSON.stringify({ title }) }),
    toggle: (id) => call<Task>(`/api/tasks/${id}`, { method: 'PATCH' }),
    remove: (id) => call<void>(`/api/tasks/${id}`, { method: 'DELETE' }),
    welcome: (email) => call<{ sent: boolean }>('/api/welcome', { method: 'POST', body: JSON.stringify({ email }) }),
  }
}

/**
 * Root component. For the M1 scaffold this renders a minimal shell that
 * confirms the app boots and that VITE_API_URL is wired through. Feature
 * components (sidebar, weather grid) arrive in later milestones.
 */
export default function App() {
  const apiUrl = import.meta.env.VITE_API_URL ?? 'unset'

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 p-4">
        <h1 className="text-xl font-semibold">Weather Dashboard</h1>
        <p className="text-sm text-slate-500" data-testid="api-url">
          API: {apiUrl}
        </p>
      </header>
    </main>
  )
}

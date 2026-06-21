// M1 scaffold: a minimal shell that renders and confirms the build/test
// harness works. The two-panel sidebar + weather grid layout is M3 scope.
function App() {
  // `||` (not `??`) so an unset *or* empty VITE_API_URL both fall back to the
  // sentinel. Under `docker compose`, VITE_API_URL is present in the container
  // env, so tests stub it explicitly rather than relying on the ambient value.
  const apiUrl = import.meta.env.VITE_API_URL || 'not configured'

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 px-6 py-4">
        <h1 className="text-2xl font-semibold">Weather Dashboard</h1>
        <p className="text-sm text-slate-500">
          Backend API: <span data-testid="api-url">{apiUrl}</span>
        </p>
      </header>
    </main>
  )
}

export default App

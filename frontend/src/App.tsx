import { API_BASE_URL } from './api/client'

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 p-4">
        <h1 className="text-xl font-semibold">Weather Dashboard</h1>
      </header>
      <main className="p-6">
        <p>Add a city to get started.</p>
        <p className="mt-2 text-sm text-slate-500" data-testid="api-base-url">
          API: {API_BASE_URL}
        </p>
      </main>
    </div>
  )
}

/**
 * App — root component / layout shell.
 *
 * Milestone 1 scaffold: this renders a minimal placeholder so the Docker stack
 * boots and the Vitest smoke test can assert the app mounts without crashing.
 * The full two-panel layout (Sidebar + MainContent) and global state arrive in
 * Milestone 3 per ARCHITECTURE.md.
 */
export default function App(): JSX.Element {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <h1 className="text-2xl font-semibold">Weather Dashboard</h1>
    </main>
  )
}

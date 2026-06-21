import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from '../App'

describe('App', () => {
  // VITE_API_URL is set in the docker-compose frontend container, so its value
  // leaks into `import.meta.env` when vitest runs inside that container. Stub
  // it per-test for deterministic results regardless of the ambient env, and
  // restore the real env after each test.
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('renders the dashboard heading', () => {
    render(<App />)
    // Asserts a real, visible outcome — the app title is in the document.
    expect(
      screen.getByRole('heading', { name: /weather dashboard/i }),
    ).toBeInTheDocument()
  })

  it('renders the configured backend API url from VITE_API_URL', () => {
    vi.stubEnv('VITE_API_URL', 'https://api.weather.example')
    render(<App />)
    // The configured URL is surfaced to the user verbatim.
    expect(screen.getByTestId('api-url')).toHaveTextContent(
      'https://api.weather.example',
    )
  })

  it('falls back to a sentinel when VITE_API_URL is not configured', () => {
    vi.stubEnv('VITE_API_URL', '')
    render(<App />)
    // With no backend URL configured, the app shows an explicit sentinel
    // rather than a blank value.
    expect(screen.getByTestId('api-url')).toHaveTextContent('not configured')
  })
})

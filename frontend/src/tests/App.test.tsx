import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'

/**
 * Smoke test (Milestone 1): verifies the Vitest + React Testing Library + jsdom
 * harness is wired correctly by mounting <App /> and asserting it renders
 * without crashing. Feature-level tests arrive in later milestones.
 */
describe('App', () => {
  it('mounts without crashing', () => {
    const { container } = render(<App />)
    expect(container).toBeInTheDocument()
  })

  it('renders the dashboard heading', () => {
    render(<App />)
    expect(
      screen.getByRole('heading', { name: /weather dashboard/i }),
    ).toBeInTheDocument()
  })
})

import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from '../App'

describe('App', () => {
  it('renders the dashboard heading', () => {
    render(<App />)
    expect(
      screen.getByRole('heading', { name: /weather dashboard/i }),
    ).toBeInTheDocument()
  })

  it('shows the empty state prompt', () => {
    render(<App />)
    expect(screen.getByText(/add a city to get started/i)).toBeInTheDocument()
  })
})

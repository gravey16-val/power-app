import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../App'

describe('App', () => {
  it('renders the dashboard title', () => {
    render(<App />)
    expect(screen.getByText('Weather Dashboard')).toBeInTheDocument()
  })

  it('shows the empty-state prompt', () => {
    render(<App />)
    expect(screen.getByText(/add a city to get started/i)).toBeInTheDocument()
  })
})

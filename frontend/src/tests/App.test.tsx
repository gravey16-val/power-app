import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../App'

describe('App', () => {
  it('renders the dashboard heading', () => {
    render(<App />)
    expect(
      screen.getByRole('heading', { name: /weather dashboard/i }),
    ).toBeInTheDocument()
  })

  it('surfaces the configured API URL', () => {
    render(<App />)
    expect(screen.getByTestId('api-url')).toBeInTheDocument()
  })
})

import { describe, expect, it } from 'vitest'
import { API_BASE_URL, client } from '../api/client'

// Guards the VITE_API_URL wiring for this ticket: the axios client must take
// its baseURL from the env-derived API_BASE_URL rather than a hardcoded value.
describe('api client', () => {
  it('derives a non-empty base URL', () => {
    expect(API_BASE_URL).toBeTruthy()
  })

  it('configures the axios instance with that base URL', () => {
    expect(client.defaults.baseURL).toBe(API_BASE_URL)
  })
})

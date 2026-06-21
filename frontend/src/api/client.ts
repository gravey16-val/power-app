import axios from 'axios'

// VITE_API_URL is baked in at build time and points at the FastAPI backend.
// Falling back to the local backend keeps `npm run dev` working out of the box.
export const API_BASE_URL: string =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const client = axios.create({
  baseURL: API_BASE_URL,
})

import axios from 'axios'

/**
 * Shared Axios instance. The base URL is baked from VITE_API_URL at build time
 * (production) or read from the environment by the dev server (local Docker).
 */
export const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

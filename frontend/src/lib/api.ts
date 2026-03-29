import axios from 'axios'

/**
 * Same-origin `/api` in dev is proxied to FastAPI so HttpOnly cookies
 * are set for 127.0.0.1 and sent on subsequent XHR/fetch.
 */
export const api = axios.create({
  baseURL: '',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

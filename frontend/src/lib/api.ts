import axios from 'axios'

import { notifyUnauthorized } from '@/lib/authSession'

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

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      notifyUnauthorized()
    }
    return Promise.reject(error)
  },
)

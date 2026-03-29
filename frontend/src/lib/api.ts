import axios from 'axios'

import { notifyAccountBlocked, notifyUnauthorized } from '@/lib/authSession'

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
    if (axios.isAxiosError(error) && error.response) {
      const status = error.response.status
      const detail = (error.response.data as { detail?: unknown })?.detail
      const detailStr = typeof detail === 'string' ? detail : ''
      if (status === 403 && detailStr === 'account_blocked') {
        notifyAccountBlocked()
      }
      if (status === 401) {
        const url = error.config?.url ?? ''
        if (!url.includes('/api/users/me')) {
          notifyUnauthorized()
        }
      }
    }
    return Promise.reject(error)
  },
)

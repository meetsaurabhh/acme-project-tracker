import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('acme_token')
    if (!token) { setLoading(false); return }
    api.get('/api/auth/me')
      .then((r) => setUser(r.data))
      .catch(() => localStorage.removeItem('acme_token'))
      .finally(() => setLoading(false))
  }, [])

  const login = async (email, password) => {
    const body = new URLSearchParams({ username: email, password })
    const { data } = await api.post('/api/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    localStorage.setItem('acme_token', data.access_token)
    const me = await api.get('/api/auth/me')
    setUser(me.data)
    return me.data
  }

  const logout = () => {
    localStorage.removeItem('acme_token')
    setUser(null)
  }

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      logout,
      canEdit: user?.role === 'admin' || user?.role === 'manager',
      isAdmin: user?.role === 'admin',
    }),
    [user, loading]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)

import { useEffect, useState } from 'react'

export function useRoute(): [string, (to: string) => void] {
  const read = () => decodeURIComponent(location.hash.replace(/^#\/?/, '')) || 'home'
  const [route, setRoute] = useState(read)

  useEffect(() => {
    const onChange = () => setRoute(read())
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  const nav = (to: string) => {
    location.hash = '/' + to
  }
  return [route, nav]
}

export const segments = (route: string) => route.split('/').filter(Boolean)

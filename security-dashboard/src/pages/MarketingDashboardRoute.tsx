import { useEffect, useRef } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import MarketingApp from '../marketing/App.jsx'
import marketingStyles from '../marketing/styles.css?raw'

export function MarketingDashboardRoute() {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const rootRef = useRef<Root | null>(null)

  useEffect(() => {
    const host = hostRef.current
    if (!host) return

    const shadow = host.shadowRoot ?? host.attachShadow({ mode: 'open' })
    shadow.innerHTML = ''

    const style = document.createElement('style')
    style.textContent = marketingStyles
    shadow.appendChild(style)

    const mount = document.createElement('div')
    mount.id = 'marketing-root'
    shadow.appendChild(mount)

    rootRef.current = createRoot(mount)
    rootRef.current.render(<MarketingApp />)

    return () => {
      rootRef.current?.unmount()
      rootRef.current = null
    }
  }, [])

  return <div ref={hostRef} className="marketing-dashboard-host" />
}

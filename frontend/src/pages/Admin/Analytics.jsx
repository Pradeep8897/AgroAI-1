import React, { useEffect, useState } from 'react'
import { Activity, Users2, Leaf, Layers, ShieldAlert, Loader2 } from 'lucide-react'
import { API_BASE } from '../../services/apiConfig'

export default function Analytics() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadStats() {
      try {
        const res = await fetch(`${API_BASE}/admin/stats`)
        const data = await res.json()
        if (data.success) {
          setMetrics(data.metrics)
        } else {
          setError(data.message || 'Failed to load platform stats.')
        }
      } catch (err) {
        setError('Failed to connect to Admin API. Please check your server.')
      } finally {
        setLoading(false)
      }
    }
    loadStats()
  }, [])

  const metricItems = metrics ? [
    { icon: Users2, title: 'Registered Farmers', value: metrics.total_users },
    { icon: Activity, title: 'Online Sessions', value: metrics.online_users },
    { icon: Layers, title: 'Total Login Attempts', value: metrics.total_login_attempts },
    { icon: ShieldAlert, title: 'Successful Logins', value: metrics.successful_logins },
  ] : []

  return (
    <div>
      <div className="page-header animate-fade-in">
        <span style={{ 
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          background: 'var(--color-primary-glow)',
          border: '1px solid var(--border-default)',
          borderRadius: 999,
          padding: '6px 14px',
          fontSize: '0.75rem',
          fontWeight: 700,
          color: 'var(--color-primary-dark)',
          marginBottom: 14,
        }}>
          ADMIN ANALYTICS
        </span>
        <h1>Platform Performance</h1>
        <p style={{ color: 'var(--text-muted)' }}>Monitor growth, user engagement, and the health of the AgroAI ecosystem.</p>
      </div>

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)', padding: 40 }} className="animate-fade-in">
          <Loader2 className="spinner" size={20} style={{ animation: 'spin 1.5s linear infinite' }} /> Loading platform metrics...
        </div>
      ) : error ? (
        <div className="alert alert-error animate-fade-in" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 16 }}>
          <ShieldAlert size={16} /> <span>{error}</span>
        </div>
      ) : (
        <div className="animate-fade-in stagger-1" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Main Metrics Grid */}
          <div style={styles.grid}>
            {metricItems.map((metric, idx) => (
              <div key={metric.title} className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={styles.metricIcon}>
                  <metric.icon size={22} color="var(--color-primary-dark)" />
                </div>
                <h3 style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>{metric.title}</h3>
                <p style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>{metric.value}</p>
              </div>
            ))}
          </div>

          {/* Revenue Breakdown */}
          <div className="card">
            <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', marginBottom: 16, borderBottom: '1px solid var(--border-subtle)', paddingBottom: 12 }}>
              � Login Metrics
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
              <div style={styles.revenueBox}>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Failed Login Attempts</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--color-primary-dark)', marginTop: 4 }}>
                  {metrics.failed_logins.toLocaleString()}
                </div>
              </div>

              <div style={styles.revenueBox}>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Last Successful Login</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-primary-dark)', marginTop: 4, whiteSpace: 'pre-wrap' }}>
                  {metrics.last_login_time || 'No successful logins yet'}
                </div>
              </div>

              <div style={{ 
                ...styles.revenueBox, 
                background: 'var(--color-primary-glow)', 
                border: '1.5px solid var(--color-primary-light)' 
              }}>
                <div style={{ fontSize: '0.82rem', color: 'var(--color-primary-dark)', fontWeight: 600 }}>Online Users</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--color-primary-dark)', marginTop: 4 }}>
                  {metrics.online_users}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const styles = {
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: 20,
  },
  metricIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    display: 'grid',
    placeItems: 'center',
    background: 'var(--color-primary-glow)',
    border: '1px solid var(--border-default)',
  },
  revenueBox: {
    padding: '16px 20px', 
    background: 'var(--bg-dark)', 
    borderRadius: 14, 
    border: '1px solid var(--border-subtle)',
    boxShadow: 'var(--shadow-sm)'
  }
}


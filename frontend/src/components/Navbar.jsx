import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth, useCart } from '../App'
import { API_BASE } from '../services/apiConfig'
import { Leaf, ShoppingCart, Bell, User, Menu, X, LogOut, ChevronDown } from 'lucide-react'

export default function Navbar() {
  const { user, logout, isLoggedIn } = useAuth()
  const { cartCount } = useCart()
  const [totalUsers, setTotalUsers] = useState(null)
  const navigate = useNavigate()
  const location = useLocation()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    async function fetchUserCount() {
      try {
        const res = await fetch(`${API_BASE}/admin/stats`)
        const data = await res.json()
        if (data.success && data.metrics) {
          setTotalUsers(data.metrics.total_users)
        }
      } catch (err) {
        setTotalUsers(null)
      }
    }

    fetchUserCount()
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/')
    setDropdownOpen(false)
  }

  return (
    <nav style={styles.nav}>
      {/* Logo */}
      <Link to={isLoggedIn ? '/dashboard' : '/'} style={styles.logo}>
        <div style={styles.logoIcon}>
          <Leaf size={20} color="#22c55e" />
        </div>
        <span style={styles.logoText}>Agro<span style={styles.logoAi}>AI</span></span>
      </Link>

      {/* Desktop Nav Links (landing only) */}
      {!isLoggedIn && (
        <div style={styles.navLinks}>
          {[['/', 'Home'], ['/features', 'Features'], ['/about', 'About'], ['/contact', 'Contact']].map(([path, label]) => (
            <Link key={path} to={path} style={{
              ...styles.navLink,
              color: location.pathname === path ? '#22c55e' : '#86efac'
            }}>{label}</Link>
          ))}
        </div>
      )}

      {/* Right Side */}
      <div style={styles.navRight}>
        {isLoggedIn ? (
          <>
            {/* Cart */}
            <Link to="/cart" style={styles.iconBtn} id="navbar-cart-btn">
              <ShoppingCart size={20} />
              {cartCount > 0 && <span style={styles.cartBadge}>{cartCount}</span>}
            </Link>

            {/* Notifications */}
            <button style={styles.iconBtn} id="navbar-notifications-btn">
              <Bell size={20} />
              <span style={{...styles.cartBadge, background: '#f59e0b'}}>3</span>
            </button>

            {/* User Dropdown */}
            <div style={{ position: 'relative' }}>
              <button
                style={styles.userBtn}
                onClick={() => setDropdownOpen(!dropdownOpen)}
                id="navbar-user-dropdown"
              >
                <div style={styles.avatar}>
                  {user?.username?.[0]?.toUpperCase() || 'U'}
                </div>
                <div>
                  <span style={styles.username}>{user?.username || 'User'}</span>
                  <span style={styles.userCount}>ID: {user?.id || 'N/A'}</span>
                  {typeof totalUsers === 'number' && (
                    <span style={styles.userCount}>Total users: {totalUsers}</span>
                  )}
                </div>
                <ChevronDown size={14} style={{ transition: 'transform 0.2s', transform: dropdownOpen ? 'rotate(180deg)' : 'none' }} />
              </button>

              {dropdownOpen && (
                <div style={styles.dropdown}>
                  <Link to="/profile" style={styles.dropdownItem} onClick={() => setDropdownOpen(false)}>
                    <User size={15} /> My Profile
                  </Link>
                  {user?.role === 'admin' && (
                    <Link to="/admin" style={styles.dropdownItem} onClick={() => setDropdownOpen(false)}>
                      Admin Panel
                    </Link>
                  )}
                  <div style={styles.dropdownDivider} />
                  <button style={{ ...styles.dropdownItem, color: '#ef4444', border: 'none', background: 'none', width: '100%', textAlign: 'left' }} onClick={handleLogout}>
                    <LogOut size={15} /> Logout
                  </button>
                </div>
              )}
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', gap: 10 }}>
            <Link to="/login" className="btn btn-ghost btn-sm" id="navbar-login-btn">Login</Link>
            <Link to="/register" className="btn btn-primary btn-sm" id="navbar-register-btn">Get Started</Link>
          </div>
        )}

        {/* Mobile Menu Toggle */}
        <button
          style={{ ...styles.iconBtn, display: 'none' }}
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          id="navbar-mobile-menu-btn"
        >
          {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>
    </nav>
  )
}

const styles = {
  nav: {
    position: 'fixed',
    top: 0, left: 0, right: 0,
    zIndex: 900,
    height: 'var(--navbar-height)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 24px',
    background: 'var(--bg-glass)',
    borderBottom: '1px solid var(--border-default)',
    backdropFilter: 'blur(16px)',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    textDecoration: 'none',
  },
  logoIcon: {
    width: 36, height: 36,
    background: 'var(--color-primary-glow)',
    border: '1px solid var(--border-default)',
    borderRadius: 10,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontSize: '1.25rem',
    fontWeight: 800,
    color: 'var(--text-primary)',
    fontFamily: 'Outfit, sans-serif',
    letterSpacing: '-0.02em',
  },
  logoAi: {
    color: 'var(--color-primary)',
  },
  navLinks: {
    display: 'flex',
    gap: 6,
    alignItems: 'center',
  },
  navLink: {
    padding: '6px 14px',
    borderRadius: 8,
    fontSize: '0.9rem',
    fontWeight: 500,
    textDecoration: 'none',
    transition: 'all 0.2s',
  },
  navRight: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  iconBtn: {
    background: 'var(--bg-dark)',
    border: '1px solid var(--border-default)',
    borderRadius: 10,
    width: 40, height: 40,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    color: 'var(--text-secondary)',
    position: 'relative',
    textDecoration: 'none',
    transition: 'border-color 0.2s, background 0.2s, color 0.2s',
  },
  cartBadge: {
    position: 'absolute',
    top: -4, right: -4,
    background: 'var(--color-primary)',
    color: '#fff',
    fontSize: '0.65rem',
    fontWeight: 700,
    width: 18, height: 18,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  userBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    background: 'var(--bg-dark)',
    border: '1px solid var(--border-default)',
    borderRadius: 10,
    padding: '6px 12px',
    cursor: 'pointer',
    color: 'var(--text-primary)',
    transition: 'all 0.2s',
  },
  avatar: {
    width: 28, height: 28,
    background: 'linear-gradient(135deg, #22c55e, #16a34a)',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.8rem',
    fontWeight: 700,
    color: '#fff',
  },
  username: {
    fontSize: '0.875rem',
    fontWeight: 600,
  },
  userCount: {
    display: 'block',
    fontSize: '0.75rem',
    color: 'var(--text-secondary)',
    marginTop: 2,
  },
  dropdown: {
    position: 'absolute',
    top: 'calc(100% + 8px)',
    right: 0,
    background: 'var(--bg-modal)',
    border: '1px solid var(--border-default)',
    borderRadius: 12,
    padding: '6px',
    minWidth: 180,
    backdropFilter: 'blur(16px)',
    boxShadow: 'var(--shadow-md)',
    zIndex: 999,
    animation: 'fadeInScale 0.2s ease',
  },
  dropdownItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '9px 12px',
    borderRadius: 8,
    fontSize: '0.875rem',
    color: 'var(--text-secondary)',
    textDecoration: 'none',
    transition: 'background 0.15s, color 0.15s',
    cursor: 'pointer',
  },
  dropdownDivider: {
    height: 1,
    background: 'var(--border-subtle)',
    margin: '4px 0',
  },
}

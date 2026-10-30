import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isProfileActive = currentPath === '/profile';
  const isResumeActive = currentPath.startsWith('/resume');
  const isInterviewActive = currentPath.startsWith('/interview');
  const isHistoryActive = currentPath.startsWith('/history');

  const navItemClass = (isActive) =>
    `px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all duration-normal cursor-pointer flex items-center space-x-1.5 ${
      isActive
        ? 'bg-amber-500/15 text-[#FCD34D] border border-amber-500/35 shadow-amber-glow-sm'
        : 'text-[#A1A1AA] hover:text-[#FAFAF5] hover:bg-white/[0.06] border border-transparent'
    }`;

  const navLinks = [
    { name: 'Profile', path: '/profile', active: isProfileActive },
    { name: 'Resume', path: '/resume-upload', active: isResumeActive },
    { name: 'Interview', path: '/interview-setup', active: isInterviewActive },
    { name: 'History', path: '/history', active: isHistoryActive },
  ];

  return (
    <header className="sticky top-0 z-40 glass-nav border-b border-white/10">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand / Logo */}
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/profile')}
            className="flex items-center space-x-2.5 group cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 rounded-lg p-1"
            aria-label="Prep AI Home"
          >
            <div className="relative flex items-center justify-center">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 group-hover:bg-amber-400 transition-colors shadow-amber-glow inline-block" />
              <span className="absolute w-4 h-4 rounded-full bg-amber-500/30 animate-ping inline-block pointer-events-none" />
            </div>
            <div className="flex items-baseline space-x-1.5">
              <span className="font-heading font-extrabold text-base tracking-tight text-[#FAFAF5]">
                PREP<span className="text-amber-500">.AI</span>
              </span>
              <span className="text-[10px] font-mono tracking-wider text-amber-400/80 uppercase font-semibold">
                NEURAL
              </span>
            </div>
          </button>
        </div>

        {/* Desktop Primary Navigation Links */}
        <nav aria-label="Main Navigation" className="hidden sm:flex items-center space-x-2">
          {navLinks.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              aria-current={item.active ? 'page' : undefined}
              className={() => navItemClass(item.active)}
            >
              <span>{item.name}</span>
            </NavLink>
          ))}

          <span className="text-white/15 px-1 font-light" aria-hidden="true">|</span>

          {/* Logout Action */}
          <button
            type="button"
            onClick={handleLogout}
            aria-label="Log out of session"
            className="px-3 py-1.5 text-xs font-semibold text-[#A1A1AA] hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors cursor-pointer border border-transparent hover:border-red-500/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
          >
            Logout
          </button>
        </nav>

        {/* Mobile Menu Toggle Button */}
        <div className="sm:hidden flex items-center space-x-2">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
            className="p-2 text-[#FAFAF5] hover:bg-white/10 rounded-lg transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Navigation Dropdown */}
      {mobileMenuOpen && (
        <div className="sm:hidden px-4 pt-3 pb-4 border-t border-white/10 bg-[#111113]/95 backdrop-blur-2xl space-y-1.5 shadow-2xl animate-fade-in-up">
          {navLinks.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              onClick={() => setMobileMenuOpen(false)}
              aria-current={item.active ? 'page' : undefined}
              className={() => `block ${navItemClass(item.active)} py-2.5 px-3.5`}
            >
              {item.name}
            </NavLink>
          ))}
          <button
            type="button"
            onClick={() => {
              setMobileMenuOpen(false);
              handleLogout();
            }}
            className="w-full text-left py-2.5 px-3.5 text-xs font-semibold text-red-400 hover:bg-red-500/10 rounded-lg transition-colors border border-transparent hover:border-red-500/20"
          >
            Logout
          </button>
        </div>
      )}
    </header>
  );
}

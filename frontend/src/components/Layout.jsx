import React from 'react';
import { Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from './Navbar';
import AnimatedBackground from './AnimatedBackground';

/**
 * Maximalist Dark Glassmorphism Layout Wrapper.
 * Embeds persistent macOS-inspired animated living background, dark glass navbar,
 * and smooth page transitions.
 */
export default function Layout() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen flex flex-col bg-[#09090B] text-[#FAFAF5] relative overflow-x-hidden selection:bg-amber-500/30 selection:text-amber-200">
      {/* Persistent macOS-inspired Black & Amber Living Background */}
      <AnimatedBackground />

      {isAuthenticated && <Navbar />}

      <main className="flex-1 flex flex-col relative z-10 px-4 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
}

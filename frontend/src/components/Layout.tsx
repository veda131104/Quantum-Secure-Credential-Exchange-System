import { ReactNode } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/router';
import ThemeToggle from './ThemeToggle';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth();
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      <nav className="bg-white dark:bg-gray-800 shadow-lg transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href={user ? '/dashboard' : '/'} className="text-2xl font-bold text-primary-600 dark:text-primary-400 transition-colors duration-200">
                DigiLocker 2.0
              </Link>
              {user && (
                <div className="ml-10 flex items-center space-x-4">
                  <Link
                    href="/dashboard"
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                      router.pathname === '/dashboard'
                        ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                        : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/wallet"
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                      router.pathname === '/wallet'
                        ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                        : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    Wallet
                  </Link>
                  {user.role === 'issuer' && (
                    <Link
                      href="/issuer/dashboard"
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                        router.pathname.startsWith('/issuer')
                          ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                          : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      Issuer Portal
                    </Link>
                  )}
                  {user.role === 'admin' && (
                    <Link
                      href="/admin/dashboard"
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                        router.pathname.startsWith('/admin')
                          ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                          : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      Admin Panel
                    </Link>
                  )}
                </div>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <ThemeToggle />
              {user ? (
                <>
                  <span className="text-sm text-gray-700 dark:text-gray-200 transition-colors duration-200">
                    {user.full_name || user.username}
                    <span className="ml-2 px-2 py-1 text-xs bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded transition-colors duration-200">
                      {user.role}
                    </span>
                  </span>
                  <button
                    onClick={logout}
                    className="text-gray-700 dark:text-gray-200 hover:text-primary-600 dark:hover:text-primary-400 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="text-gray-700 dark:text-gray-200 hover:text-primary-600 dark:hover:text-primary-400 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
                  >
                    Login
                  </Link>
                  <Link
                    href="/register"
                    className="bg-primary-600 dark:bg-primary-500 text-white hover:bg-primary-700 dark:hover:bg-primary-600 px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200"
                  >
                    Register
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>
      <main>{children}</main>
    </div>
  );
}

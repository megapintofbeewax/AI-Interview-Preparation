import React from 'react';

/**
 * Global React Error Boundary
 * Prevents white-screen crashes and renders clean, friendly recovery view.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("UI Error caught by boundary:", error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center px-4 py-12">
          <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg p-8 shadow-sm text-center space-y-4">
            <div className="w-10 h-10 mx-auto rounded-full bg-red-50 border border-red-100 flex items-center justify-center text-red-600 font-semibold text-lg">
              !
            </div>
            <h2 className="text-xl font-semibold tracking-tight text-gray-900">
              SOMETHING WENT WRONG
            </h2>
            <p className="text-sm text-gray-500">
              We encountered an unexpected problem while loading this view. Please try reloading.
            </p>
            <div className="pt-2 flex flex-col sm:flex-row gap-2">
              <button
                onClick={this.handleReload}
                className="flex-1 py-2 px-4 bg-gray-900 hover:bg-gray-800 text-white text-xs font-medium rounded-md transition-colors cursor-pointer"
              >
                Reload Page
              </button>
              <button
                onClick={this.handleGoHome}
                className="flex-1 py-2 px-4 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-medium rounded-md transition-colors cursor-pointer"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

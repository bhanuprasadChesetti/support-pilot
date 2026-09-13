import PropTypes from 'prop-types';

export function ChatHeader({
  title = 'SupportPilot',
  subtitle = 'AI Customer Support Platform for D2C Ecommerce Brands',
  onToggleSidebar,
  isSidebarOpen,
}) {
  return (
    <header className="px-6 py-4 bg-slate-900/90 border-b border-slate-800 backdrop-blur shrink-0 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        {!isSidebarOpen && (
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors mr-1"
            title="Open chats sidebar"
            aria-label="Open sidebar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}
        <div className="h-9 w-9 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 ring-1 ring-indigo-400/30">
          <span className="text-white font-bold text-lg tracking-wider">SP</span>
        </div>
        <div>
          <h1 className="text-lg font-semibold text-slate-100 tracking-tight leading-tight">
            {title}
          </h1>
          <p className="text-xs text-slate-400 font-medium">
            {subtitle}
          </p>
        </div>
      </div>

      <div className="hidden sm:flex items-center space-x-2 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700/60">
        <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-xs text-slate-300 font-medium">Phase 1 Skeleton</span>
      </div>
    </header>
  );
}

ChatHeader.propTypes = {
  title: PropTypes.string,
  subtitle: PropTypes.string,
  onToggleSidebar: PropTypes.func,
  isSidebarOpen: PropTypes.bool,
};


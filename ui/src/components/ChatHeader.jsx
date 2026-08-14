import PropTypes from 'prop-types';

export function ChatHeader({ title = 'SupportPilot', subtitle = 'AI Customer Support Platform for D2C Ecommerce Brands' }) {
  return (
    <header className="px-6 py-5 bg-slate-900/90 border-b border-slate-800 backdrop-blur shrink-0 flex items-center justify-between">
      <div className="flex items-center space-x-3">
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
};

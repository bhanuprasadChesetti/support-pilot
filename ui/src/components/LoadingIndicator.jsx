import { Bot } from 'lucide-react';

export function LoadingIndicator() {
  return (
    <div className="flex items-end space-x-2.5 my-3 justify-start">
      <div className="h-8 w-8 rounded-full bg-slate-800 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 shadow-sm">
        <Bot className="w-4 h-4" />
      </div>

      <div className="bg-slate-800/90 border border-slate-700/60 text-slate-300 px-4 py-3 rounded-2xl rounded-bl-xs flex items-center space-x-1.5 shadow-sm">
        <span className="text-xs text-slate-400 font-medium mr-1">SupportPilot thinking</span>
        <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
        <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
        <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" />
      </div>
    </div>
  );
}

import PropTypes from 'prop-types';
import { Bot, User } from 'lucide-react';

export function MessageBubble({ message }) {
  const isCustomer = message.sender === 'customer' || message.sender === 'user';

  return (
    <div
      className={`flex items-end space-x-2.5 my-3 ${
        isCustomer ? 'justify-end' : 'justify-start'
      }`}
    >
      {!isCustomer && (
        <div className="h-8 w-8 rounded-full bg-slate-800 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 shadow-sm">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div
        className={`max-w-[80%] sm:max-w-[70%] px-4 py-3 text-sm leading-relaxed shadow-sm transition-all ${
          isCustomer
            ? 'bg-indigo-600 text-white rounded-2xl rounded-br-xs'
            : 'bg-slate-800/90 text-slate-100 border border-slate-700/60 rounded-2xl rounded-bl-xs'
        }`}
      >
        <p className="whitespace-pre-wrap break-words">{message.text}</p>
        <div
          className={`mt-1 text-[10px] select-none ${
            isCustomer ? 'text-indigo-200 text-right' : 'text-slate-400 text-left'
          }`}
        >
          {message.timestamp}
        </div>
      </div>

      {isCustomer && (
        <div className="h-8 w-8 rounded-full bg-indigo-950/80 border border-indigo-500/40 flex items-center justify-center text-indigo-300 shrink-0 shadow-sm">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
}

MessageBubble.propTypes = {
  message: PropTypes.shape({
    id: PropTypes.string,
    sender: PropTypes.oneOf(['customer', 'user', 'ai', 'assistant']).isRequired,
    text: PropTypes.string.isRequired,
    timestamp: PropTypes.string.isRequired,
  }).isRequired,
};

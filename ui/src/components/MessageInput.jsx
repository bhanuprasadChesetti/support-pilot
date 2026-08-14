import { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Send } from 'lucide-react';

export function MessageInput({ onSendMessage, disabled }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  const adjustTextareaHeight = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [text]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;

    onSendMessage(trimmed);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4 bg-slate-900/90 border-t border-slate-800 shrink-0"
    >
      <div className="relative flex items-end rounded-2xl bg-slate-800/90 border border-slate-700/70 focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 transition-all p-2 shadow-lg">
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          disabled={disabled}
          className="w-full resize-none bg-transparent px-3 py-2 text-sm text-slate-100 placeholder-slate-400 focus:outline-none disabled:opacity-50 max-h-40 leading-relaxed"
        />

        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="ml-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-xs font-semibold rounded-xl flex items-center space-x-1.5 transition-all disabled:opacity-40 disabled:cursor-not-allowed shrink-0 h-9"
        >
          <span>Send</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className="mt-1.5 px-2 flex justify-between items-center text-[11px] text-slate-400">
        <span>Press <kbd className="px-1 py-0.5 bg-slate-800 rounded border border-slate-700 text-slate-300 font-mono">Enter</kbd> to send</span>
        <span><kbd className="px-1 py-0.5 bg-slate-800 rounded border border-slate-700 text-slate-300 font-mono">Shift + Enter</kbd> for new line</span>
      </div>
    </form>
  );
}

MessageInput.propTypes = {
  onSendMessage: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
};

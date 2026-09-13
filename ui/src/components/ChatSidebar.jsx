import PropTypes from 'prop-types';

export function ChatSidebar({
  isOpen,
  onClose,
  conversations,
  activeId,
  onSelectConversation,
  onNewChat,
}) {
  if (!isOpen) return null;

  return (
    <aside className="w-80 border-r border-slate-800 bg-slate-900/95 flex flex-col h-full shrink-0 z-20 transition-all duration-200 ease-in-out">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <div className="h-7 w-7 rounded-md bg-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow">
            SP
          </div>
          <span className="font-semibold text-slate-100 text-sm tracking-wide">
            Support Pilot
          </span>
        </div>
        
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          title="Close sidebar"
          aria-label="Close sidebar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors shadow-md shadow-indigo-600/20"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
        <div className="px-2 py-1 text-xs font-medium text-slate-400 uppercase tracking-wider">
          Recent Conversations
        </div>
        
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-500">
            No conversations yet. Start a new chat!
          </div>
        ) : (
          conversations.map((chat) => {
            const isActive = chat.id === activeId;
            return (
              <button
                key={chat.id}
                onClick={() => onSelectConversation(chat.id)}
                className={`w-full text-left p-3 rounded-xl transition-all flex flex-col gap-1 border ${
                  isActive
                    ? 'bg-slate-800/90 border-indigo-500/50 shadow-sm'
                    : 'border-transparent hover:bg-slate-800/50 hover:border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium truncate ${isActive ? 'text-indigo-300' : 'text-slate-200'}`}>
                    {chat.title || `Chat #${chat.id}`}
                  </span>
                  <span className="text-[10px] text-slate-500 shrink-0">
                    {chat.timestamp}
                  </span>
                </div>
                <p className="text-xs text-slate-400 truncate">
                  {chat.lastMessage || 'No messages yet'}
                </p>
              </button>
            );
          })
        )}
      </div>

      {/* Sidebar Footer */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-900/40 text-xs text-slate-500 text-center">
        SupportPilot v1.0 • Frontend
      </div>
    </aside>
  );
}

ChatSidebar.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  conversations: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string,
      lastMessage: PropTypes.string,
      timestamp: PropTypes.string,
    })
  ).isRequired,
  activeId: PropTypes.string,
  onSelectConversation: PropTypes.func.isRequired,
  onNewChat: PropTypes.func.isRequired,
};

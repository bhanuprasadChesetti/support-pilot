import { useState, useEffect } from 'react';
import { ChatHeader } from './ChatHeader';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { ChatSidebar } from './ChatSidebar';
import {
  streamChatMessage,
  fetchConversations,
  createConversation,
  fetchConversationMessages,
} from '../services/chatApi';
import { formatMessageTime } from '../utils/formatters';

export function ChatContainer() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messagesMap, setMessagesMap] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Fetch conversations list from API on mount
  useEffect(() => {
    let isMounted = true;
    const loadConversations = async () => {
      try {
        const list = await fetchConversations();
        if (isMounted) {
          setConversations(list || []);
          if (list && list.length > 0) {
            setActiveConversationId(list[0].id);
          }
        }
      } catch (err) {
        console.error('Failed to load conversations from backend:', err);
      }
    };
    loadConversations();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch messages whenever active conversation changes
  useEffect(() => {
    if (!activeConversationId) return;

    let isMounted = true;
    const loadMessages = async () => {
      try {
        const msgs = await fetchConversationMessages(activeConversationId);
        if (isMounted) {
          setMessagesMap((prev) => ({
            ...prev,
            [activeConversationId]: msgs || [],
          }));
        }
      } catch (err) {
        console.error(`Failed to load messages for conversation ${activeConversationId}:`, err);
      }
    };

    loadMessages();
    return () => {
      isMounted = false;
    };
  }, [activeConversationId]);

  const currentMessages = activeConversationId ? (messagesMap[activeConversationId] || []) : [];

  const handleSelectConversation = (id) => {
    setActiveConversationId(id);
    setError(null);
  };

  const handleNewChat = async () => {
    try {
      const newChat = await createConversation();
      setConversations((prev) => [newChat, ...prev]);
      setActiveConversationId(newChat.id);
      setMessagesMap((prev) => ({
        ...prev,
        [newChat.id]: [],
      }));
      setError(null);
    } catch (err) {
      console.error('Failed to create new chat:', err);
      setError('Failed to create a new chat session.');
    }
  };

  const handleSendMessage = async (text) => {
    if (!text.trim() || loading) return;

    setError(null);
    const userMsg = {
      id: Date.now().toString(),
      sender: 'customer',
      text: text.trim(),
      timestamp: formatMessageTime(),
    };

    const targetConvId = activeConversationId;
    const aiMsgId = (Date.now() + 1).toString();
    const aiMsg = {
      id: aiMsgId,
      sender: 'ai',
      text: '',
      timestamp: formatMessageTime(),
    };

    if (targetConvId) {
      setMessagesMap((prev) => ({
        ...prev,
        [targetConvId]: [...(prev[targetConvId] || []), userMsg, aiMsg],
      }));

      // Update conversation last message in sidebar preview
      setConversations((prev) =>
        prev.map((c) =>
          c.id === targetConvId
            ? { ...c, lastMessage: text.trim(), timestamp: 'Just now' }
            : c
        )
      );
    }

    setLoading(true);

    try {
      await streamChatMessage({
        message: text.trim(),
        conversationId: targetConvId,
        onChunk: (chunk) => {
          if (!targetConvId) return;
          setMessagesMap((prev) => {
            const currentMsgs = prev[targetConvId] || [];
            return {
              ...prev,
              [targetConvId]: currentMsgs.map((m) =>
                m.id === aiMsgId ? { ...m, text: m.text + chunk } : m
              ),
            };
          });
        },
      });

      // Refresh list to keep title & timestamp accurate from DB
      const updatedList = await fetchConversations();
      if (updatedList) setConversations(updatedList);

    } catch (err) {
      console.error('Failed to send message:', err);
      setError(
        err?.message ||
        'Failed to reach SupportPilot backend service. Please check your network or server status.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-slate-950 text-slate-100 overflow-hidden">
      {/* Left Sidebar */}
      <ChatSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        conversations={conversations}
        activeId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <ChatHeader
          onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
          isSidebarOpen={isSidebarOpen}
        />
        <MessageList messages={currentMessages} loading={loading} error={error} />
        <MessageInput onSendMessage={handleSendMessage} disabled={loading} />
      </div>
    </div>
  );
}



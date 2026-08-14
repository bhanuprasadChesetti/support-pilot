import { useState } from 'react';
import { ChatHeader } from './ChatHeader';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { sendChatMessage } from '../services/chatApi';
import { formatMessageTime } from '../utils/formatters';

const INITIAL_MESSAGES = [
  {
    id: '1',
    sender: 'customer',
    text: "My order hasn't arrived.",
    timestamp: '10:00 AM',
  },
  {
    id: '2',
    sender: 'ai',
    text: "I'm sorry to hear that. Could you share your order number?",
    timestamp: '10:01 AM',
  },
  {
    id: '3',
    sender: 'customer',
    text: 'I placed it three days ago.',
    timestamp: '10:02 AM',
  },
  {
    id: '4',
    sender: 'ai',
    text: 'Thank you. Could you provide the order number so I can investigate?',
    timestamp: '10:02 AM',
  },
];

export function ChatContainer() {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId] = useState('123');

  const handleSendMessage = async (text) => {
    if (!text.trim() || loading) return;

    setError(null);
    const userMsg = {
      id: Date.now().toString(),
      sender: 'customer',
      text: text.trim(),
      timestamp: formatMessageTime(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await sendChatMessage({
        message: text.trim(),
        conversationId,
      });

      const aiMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: data.response,
        timestamp: formatMessageTime(),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error('Failed to send message:', err);
      setError(
        err?.response?.data?.detail ||
        'Failed to reach SupportPilot backend service. Please check your network or server status.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-5xl mx-auto border-x border-slate-800 bg-slate-950 shadow-2xl overflow-hidden">
      <ChatHeader />
      <MessageList messages={messages} loading={loading} error={error} />
      <MessageInput onSendMessage={handleSendMessage} disabled={loading} />
    </div>
  );
}

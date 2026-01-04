import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { Send, Menu, X, Bot, User as UserIcon } from 'lucide-react';
import axios from 'axios';
import 'katex/dist/katex.min.css';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const Chat = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const ws = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const res = await axios.get(`/chat/history/${user.session_id}`);
        const formatted = res.data.map(msg => ({
          role: msg.role === 'model' ? 'ai' : 'user',
          content: msg.content
        }));
        setMessages(formatted);
      } catch (err) {
        console.error("Failed to load history", err);
      }
    };
    if (user?.session_id) loadHistory();
  }, [user]);

  useEffect(() => {
    if (!user?.session_id) return;

    ws.current = new WebSocket(`ws://localhost:8000/ws/chat/${user.session_id}`);

    ws.current.onmessage = (event) => {
      const text = event.data;
      if (text === "") return; 

      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        
        if (lastMsg && lastMsg.role === 'ai' && !lastMsg.isComplete) {
          return [
            ...prev.slice(0, -1),
            { ...lastMsg, content: lastMsg.content + text }
          ];
        } else {
          return [...prev, { role: 'ai', content: text, isComplete: false }];
        }
      });
    };

    return () => ws.current?.close();
  }, [user]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setMessages(prev => [...prev, { role: 'user', content: input }]);
    
    setMessages(prev => prev.map(m => ({...m, isComplete: true})));

    ws.current.send(input);
    setInput('');
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex w-full h-[calc(100vh-4rem)] bg-white">
      <div className={`${isSidebarOpen ? 'w-64' : 'w-0'} bg-gray-50 border-r transition-all duration-300 overflow-hidden flex flex-col`}>
        <div className="p-4 border-b font-semibold text-gray-700 flex justify-between items-center">
          <span>Chat History</span>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden">
            <X size={18} />
          </button>
        </div>
        <div className="p-4 text-sm text-gray-500">
          <p>Session ID: {user?.session_id?.slice(0,8)}...</p>
          <div className="mt-4 space-y-2">
            <div className="p-2 bg-indigo-50 text-indigo-700 rounded cursor-pointer">
              Current Session
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        {!isSidebarOpen && (
          <button 
            onClick={() => setSidebarOpen(true)}
            className="absolute top-20 left-4 p-2 bg-white shadow rounded-full z-10"
          >
            <Menu size={20} />
          </button>
        )}

        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'ai' && (
                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0">
                  <Bot size={18} className="text-indigo-600" />
                </div>
              )}
              
              <div className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                msg.role === 'user' 
                  ? 'bg-indigo-600 text-white rounded-br-none' 
                  : 'bg-gray-100 text-gray-800 rounded-bl-none'
              }`}>
                <div className="prose prose-sm max-w-none wrap-break-word dark:prose-invert">
                    <ReactMarkdown
                    remarkPlugins={[remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                        p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                        h3: ({node, ...props}) => <h3 className="text-lg font-bold mt-4 mb-2" {...props} />,
                        ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2" {...props} />,
                        li: ({node, ...props}) => <li className="mb-1" {...props} />,
                        code: ({node, ...props}) => <code className="bg-black/10 rounded px-1 py-0.5 font-mono text-sm" {...props} />,
                        pre: ({node, ...props}) => <pre className="bg-gray-800 text-white p-3 rounded-lg overflow-x-auto my-2" {...props} />
                    }}
                    >
                    {msg.content}
                    </ReactMarkdown>
                </div>
              </div>

              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
                  <UserIcon size={18} className="text-gray-600" />
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t bg-white">
          <form onSubmit={sendMessage} className="flex gap-2 max-w-4xl mx-auto">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask your math tutor anything..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
            />
            <button 
              type="submit" 
              className="bg-indigo-600 text-white p-3 rounded-xl hover:bg-indigo-700 transition"
              disabled={!input.trim()}
            >
              <Send size={20} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Chat;
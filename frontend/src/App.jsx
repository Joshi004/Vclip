/**
 * Main application component
 * Orchestrates chat functionality and manages state
 */

import { useState, useEffect, useRef } from 'react';
import { Container, Paper, Typography, Alert, Box } from '@mui/material';
import ChatList from './components/ChatList';
import ChatInput from './components/ChatInput';
import { sendChatMessage } from './services/api';
import { MESSAGE_ROLES, UI_CONSTANTS } from './config/constants';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: MESSAGE_ROLES.USER,
      content: input.trim(),
    };

    // Add user message to chat
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      // Send message to backend
      const response = await sendChatMessage(userMessage.content, messages);

      // Add assistant response to chat
      const assistantMessage = {
        role: MESSAGE_ROLES.ASSISTANT,
        content: response.reply,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(
        'Failed to get response from chatbot. Please check if the backend is running.'
      );
      console.error('Chat error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container
      maxWidth={UI_CONSTANTS.CONTAINER_MAX_WIDTH}
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        py: 4,
      }}
    >
      <Typography variant="h4" gutterBottom align="center" sx={{ mb: 3 }}>
        Chatbot
      </Typography>

      {error && (
        <Alert
          severity="error"
          onClose={() => setError(null)}
          sx={{ mb: 2 }}
        >
          {error}
        </Alert>
      )}

      <Paper
        elevation={3}
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          mb: 2,
        }}
      >
        <ChatList
          messages={messages}
          loading={loading}
          messagesEndRef={messagesEndRef}
        />

        <ChatInput
          input={input}
          setInput={setInput}
          onSend={handleSendMessage}
          loading={loading}
        />
      </Paper>

      <Box sx={{ textAlign: 'center', mt: 1 }}>
        <Typography variant="caption" color="text.secondary">
          Powered by Llama 3 via Ollama
        </Typography>
      </Box>
    </Container>
  );
}

export default App;


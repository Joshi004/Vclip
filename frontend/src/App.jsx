/**
 * Main application component
 * Orchestrates chat functionality with session management and context awareness
 */

import { useState, useEffect, useRef } from 'react';
import {
  Container,
  Paper,
  Typography,
  Alert,
  Box,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Stack,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import ChatList from './components/ChatList';
import ChatInput from './components/ChatInput';
import { sendChatMessage } from './services/api';
import { MESSAGE_ROLES, UI_CONSTANTS, STORAGE_KEYS } from './config/constants';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [showContext, setShowContext] = useState(false);
  const [contextUsed, setContextUsed] = useState([]);
  const messagesEndRef = useRef(null);

  // Load session ID and preferences from localStorage on mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem(STORAGE_KEYS.SESSION_ID);
    const savedShowContext = localStorage.getItem(STORAGE_KEYS.SHOW_CONTEXT);

    if (savedSessionId) {
      setSessionId(savedSessionId);
    }

    if (savedShowContext === 'true') {
      setShowContext(true);
    }
  }, []);

  // Save session ID to localStorage whenever it changes
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
    }
  }, [sessionId]);

  // Save show context preference
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.SHOW_CONTEXT, showContext.toString());
  }, [showContext]);

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
      // Send message to backend with session ID
      const response = await sendChatMessage(userMessage.content, sessionId);

      // Update session ID if this is a new session
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
      }

      // Store context if available
      if (response.context_used && response.context_used.length > 0) {
        setContextUsed(response.context_used);
      } else {
        setContextUsed([]);
      }

      // Add assistant response to chat
      const assistantMessage = {
        role: MESSAGE_ROLES.ASSISTANT,
        content: response.reply,
        context: response.context_used || [],
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

  const handleNewConversation = () => {
    // Clear current session
    setSessionId(null);
    setMessages([]);
    setContextUsed([]);
    localStorage.removeItem(STORAGE_KEYS.SESSION_ID);
    setError(null);
  };

  const toggleShowContext = () => {
    setShowContext((prev) => !prev);
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
      {/* Header with title and actions */}
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 3 }}
      >
        <Typography variant="h4" gutterBottom sx={{ mb: 0 }}>
          Context-Aware Chatbot
        </Typography>

        <Stack direction="row" spacing={1} alignItems="center">
          {/* Show context toggle */}
          <Tooltip title="Toggle context display">
            <IconButton
              onClick={toggleShowContext}
              color={showContext ? 'primary' : 'default'}
              size="small"
            >
              <InfoOutlinedIcon />
            </IconButton>
          </Tooltip>

          {/* New conversation button */}
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={handleNewConversation}
            size="small"
          >
            New Conversation
          </Button>
        </Stack>
      </Stack>

      {/* Session indicator */}
      {sessionId && (
        <Box sx={{ mb: 2, textAlign: 'center' }}>
          <Chip
            label={`Session: ${sessionId.substring(0, 8)}...`}
            size="small"
            variant="outlined"
            color="primary"
          />
        </Box>
      )}

      {/* Error alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Context info alert */}
      {showContext && contextUsed.length > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2" fontWeight="bold" gutterBottom>
            Context Used ({contextUsed.length} messages):
          </Typography>
          {contextUsed.map((ctx, idx) => (
            <Typography key={idx} variant="caption" display="block">
              • [{ctx.role}] {ctx.content.substring(0, 100)}...
              (relevance: {(ctx.score * 100).toFixed(0)}%)
            </Typography>
          ))}
        </Alert>
      )}

      {/* Chat interface */}
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

      {/* Footer */}
      <Box sx={{ textAlign: 'center', mt: 1 }}>
        <Typography variant="caption" color="text.secondary">
          Powered by Llama 3 via Ollama • Context-aware with Qdrant
        </Typography>
      </Box>
    </Container>
  );
}

export default App;


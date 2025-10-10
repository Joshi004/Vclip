/**
 * Chat message list component
 * Displays all messages in a scrollable container
 */

import { Box, CircularProgress, Typography } from '@mui/material';
import ChatMessage from './ChatMessage';

const ChatList = ({ messages, loading, messagesEndRef }) => {
  return (
    <Box
      sx={{
        flex: 1,
        overflowY: 'auto',
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {messages.length === 0 && (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: 'text.secondary',
          }}
        >
          <Typography variant="h6" gutterBottom>
            Welcome to Chatbot
          </Typography>
          <Typography variant="body2">
            Start a conversation by typing a message below
          </Typography>
        </Box>
      )}

      {messages.map((msg, idx) => (
        <ChatMessage key={idx} message={msg} />
      ))}

      {loading && (
        <Box
          sx={{
            alignSelf: 'flex-start',
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            p: 2,
          }}
        >
          <CircularProgress size={20} />
          <Typography variant="body2" color="text.secondary">
            Assistant is typing...
          </Typography>
        </Box>
      )}

      <div ref={messagesEndRef} />
    </Box>
  );
};

export default ChatList;


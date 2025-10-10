/**
 * Individual chat message component
 * Displays a single message with styling based on role (user/assistant)
 */

import { Box, Paper, Typography } from '@mui/material';
import { MESSAGE_ROLES, UI_CONSTANTS } from '../config/constants';

const ChatMessage = ({ message }) => {
  const isUser = message.role === MESSAGE_ROLES.USER;

  return (
    <Box
      sx={{
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        maxWidth: UI_CONSTANTS.MAX_MESSAGE_WIDTH,
      }}
    >
      <Paper
        elevation={1}
        sx={{
          p: 2,
          bgcolor: isUser ? 'primary.main' : 'grey.200',
          color: isUser ? 'white' : 'text.primary',
          borderRadius: 2,
        }}
      >
        <Typography
          variant="caption"
          display="block"
          sx={{ mb: 0.5, opacity: 0.8, fontWeight: 600 }}
        >
          {isUser ? 'You' : 'Assistant'}
        </Typography>
        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
          {message.content}
        </Typography>
      </Paper>
    </Box>
  );
};

export default ChatMessage;


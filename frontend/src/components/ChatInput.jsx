/**
 * Chat input component
 * Handles user input and message sending
 */

import { Box, TextField, IconButton } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { UI_CONSTANTS } from '../config/constants';

const ChatInput = ({ input, setInput, onSend, loading }) => {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <Box
      sx={{
        p: 2,
        borderTop: 1,
        borderColor: 'divider',
        display: 'flex',
        gap: 1,
        bgcolor: 'background.paper',
      }}
    >
      <TextField
        fullWidth
        multiline
        maxRows={UI_CONSTANTS.INPUT_MAX_ROWS}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
        disabled={loading}
        variant="outlined"
        size="small"
      />
      <IconButton
        color="primary"
        onClick={onSend}
        disabled={loading || !input.trim()}
        size="large"
        sx={{
          bgcolor: 'primary.main',
          color: 'white',
          '&:hover': {
            bgcolor: 'primary.dark',
          },
          '&:disabled': {
            bgcolor: 'grey.300',
          },
        }}
      >
        <SendIcon />
      </IconButton>
    </Box>
  );
};

export default ChatInput;


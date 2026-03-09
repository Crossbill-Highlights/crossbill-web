import { Box, CircularProgress, Typography, useTheme } from '@mui/material';
import { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

import { markdownStyles } from '@/theme/theme';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatMessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
}

export const ChatMessageList = ({ messages, isLoading, error }: ChatMessageListProps) => {
  const theme = useTheme();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, error]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        mb: 2,
      }}
    >
      {messages.map((msg, i) => (
        <Box
          key={i}
          sx={{
            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '80%',
            p: 1.5,
            borderRadius: 2,
            bgcolor: msg.role === 'user' ? 'primary.main' : 'grey.100',
            color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
            ...(theme.palette.mode === 'dark' && msg.role === 'assistant'
              ? { bgcolor: 'grey.800' }
              : {}),
          }}
        >
          {msg.role === 'assistant' ? (
            <Box sx={markdownStyles(theme)}>
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </Box>
          ) : (
            <Typography variant="body1">{msg.content}</Typography>
          )}
        </Box>
      ))}

      {isLoading && (
        <Box sx={{ alignSelf: 'flex-start' }}>
          <CircularProgress size={24} />
        </Box>
      )}

      <div ref={messagesEndRef} />
    </Box>
  );
};

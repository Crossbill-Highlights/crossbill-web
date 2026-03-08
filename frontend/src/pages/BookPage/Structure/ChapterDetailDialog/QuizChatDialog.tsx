import CloseIcon from '@mui/icons-material/Close';
import SendIcon from '@mui/icons-material/Send';
import {
  Box,
  CircularProgress,
  Dialog,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
  useTheme,
} from '@mui/material';
import { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

import {
  useCreateQuizSessionApiV1ChaptersChapterIdQuizSessionsPost,
  useSendQuizMessageApiV1QuizSessionsSessionIdMessagesPost,
} from '@/api/generated/quiz/quiz';
import { markdownStyles } from '@/theme/theme';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface QuizChatDialogProps {
  open: boolean;
  onClose: () => void;
  chapterId: number;
  chapterName: string;
}

export const QuizChatDialog = ({ open, onClose, chapterId, chapterName }: QuizChatDialogProps) => {
  const theme = useTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sessionStartedRef = useRef(false);

  const { mutate: createSession, isPending: isCreating } =
    useCreateQuizSessionApiV1ChaptersChapterIdQuizSessionsPost({
      mutation: {
        onSuccess: (data) => {
          setSessionId(data.session_id);
          setMessages([{ role: 'assistant', content: data.message }]);
        },
      },
    });

  const { mutate: sendMessage, isPending: isSending } =
    useSendQuizMessageApiV1QuizSessionsSessionIdMessagesPost({
      mutation: {
        onSuccess: (data) => {
          setMessages((prev) => [...prev, { role: 'assistant', content: data.message }]);
          setIsComplete(data.is_complete);
        },
      },
    });

  // Start session when dialog opens
  useEffect(() => {
    if (open && !sessionStartedRef.current) {
      sessionStartedRef.current = true;
      createSession({ chapterId });
    }
  }, [open, createSession, chapterId]);

  // Reset state after dialog close animation completes
  const handleExited = useCallback(() => {
    setMessages([]);
    setInput('');
    setSessionId(null);
    setIsComplete(false);
    sessionStartedRef.current = false;
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = useCallback(() => {
    if (!input.trim() || !sessionId || isSending) return;

    const userMessage = input.trim();
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setInput('');

    sendMessage({ sessionId, data: { message: userMessage } });
  }, [input, sessionId, isSending, sendMessage]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <Dialog fullScreen open={open} onClose={onClose} TransitionProps={{ onExited: handleExited }}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Typography variant="h6" noWrap sx={{ flex: 1 }}>
          Quiz: {chapterName}
        </Typography>
        <IconButton onClick={onClose} edge="end">
          <CloseIcon />
        </IconButton>
      </Box>

      {/* Messages */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {isCreating && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <CircularProgress />
          </Box>
        )}

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

        {isSending && (
          <Box sx={{ alignSelf: 'flex-start' }}>
            <CircularProgress size={24} />
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <TextField
          fullWidth
          placeholder={isComplete ? 'Quiz complete!' : 'Type your answer...'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSending || isCreating || isComplete}
          multiline
          maxRows={3}
          slotProps={{
            input: {
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={handleSend}
                    disabled={!input.trim() || isSending || isCreating || isComplete}
                    color="primary"
                  >
                    <SendIcon />
                  </IconButton>
                </InputAdornment>
              ),
            },
          }}
        />
      </Box>
    </Dialog>
  );
};

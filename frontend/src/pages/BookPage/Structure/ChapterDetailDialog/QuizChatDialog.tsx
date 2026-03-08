import CloseIcon from '@mui/icons-material/Close';
import ReplayIcon from '@mui/icons-material/Replay';
import SendIcon from '@mui/icons-material/Send';
import {
  Alert,
  Box,
  Button,
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

const ERROR_MESSAGE = 'Something went wrong. The AI service may be temporarily unavailable.';

export const QuizChatDialog = ({ open, onClose, chapterId, chapterName }: QuizChatDialogProps) => {
  const theme = useTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sessionStartedRef = useRef(false);

  const { mutate: createSession, isPending: isCreating } =
    useCreateQuizSessionApiV1ChaptersChapterIdQuizSessionsPost({
      mutation: {
        onSuccess: (data) => {
          setError(null);
          setSessionId(data.session_id);
          setMessages([{ role: 'assistant', content: data.message }]);
        },
        onError: () => {
          setError(ERROR_MESSAGE);
        },
      },
    });

  const { mutate: sendMessage, isPending: isSending } =
    useSendQuizMessageApiV1QuizSessionsSessionIdMessagesPost({
      mutation: {
        onSuccess: (data) => {
          setError(null);
          setMessages((prev) => [...prev, { role: 'assistant', content: data.message }]);
          setIsComplete(data.is_complete);
        },
        onError: () => {
          // Remove the optimistically-added user message and restore it to input
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === 'user') {
              setInput(last.content);
              return prev.slice(0, -1);
            }
            return prev;
          });
          setError(ERROR_MESSAGE);
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
    setError(null);
    sessionStartedRef.current = false;
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, error]);

  const handleSend = useCallback(() => {
    if (!input.trim() || !sessionId || isSending) return;

    setError(null);
    const userMessage = input.trim();
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setInput('');

    sendMessage({ sessionId, data: { message: userMessage } });
  }, [input, sessionId, isSending, sendMessage]);

  const handleRetryCreate = useCallback(() => {
    setError(null);
    createSession({ chapterId });
  }, [createSession, chapterId]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const hasSessionError = error && !sessionId;
  const hasSendError = error && sessionId;

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

        {hasSessionError && (
          <Box
            sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 4, gap: 2 }}
          >
            <Alert severity="error" sx={{ width: '100%', maxWidth: 400 }}>
              {error}
            </Alert>
            <Button variant="outlined" startIcon={<ReplayIcon />} onClick={handleRetryCreate}>
              Try again
            </Button>
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

        {hasSendError && (
          <Alert severity="error" sx={{ alignSelf: 'flex-start', maxWidth: '80%' }}>
            {error}
          </Alert>
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
          disabled={isSending || isCreating || isComplete || !!hasSessionError}
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

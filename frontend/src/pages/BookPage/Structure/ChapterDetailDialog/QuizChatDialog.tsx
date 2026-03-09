import { useCallback, useEffect, useState } from 'react';

import {
  useCreateQuizSessionApiV1ChaptersChapterIdQuizSessionsPost,
  useSendQuizMessageApiV1QuizSessionsSessionIdMessagesPost,
} from '@/api/generated/quiz/quiz';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { CommonDialogTitle } from '@/components/dialogs/CommonDialogTitle.tsx';

import { ChatInput } from './quiz/ChatInput.tsx';
import { type ChatMessage, ChatMessageList } from './quiz/ChatMessageList.tsx';
import { SessionError } from './quiz/SessionError.tsx';

interface QuizChatDialogProps {
  open: boolean;
  onClose: () => void;
  chapterId: number;
  chapterName: string;
}

const ERROR_MESSAGE = 'Something went wrong. The AI service may be temporarily unavailable.';

/** Wrapper that remounts inner content each time the dialog opens, giving fresh state. */
export const QuizChatDialog = ({ open, onClose, chapterId, chapterName }: QuizChatDialogProps) => {
  const title = <CommonDialogTitle>Quiz: {chapterName}</CommonDialogTitle>;

  return (
    <CommonDialog open={open} onClose={onClose} maxWidth="md" title={title}>
      {open && <QuizChatContent chapterId={chapterId} />}
    </CommonDialog>
  );
};

interface QuizChatContentProps {
  chapterId: number;
}

const QuizChatContent = ({ chapterId }: QuizChatContentProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

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
        },
        onError: () => {
          // Remove the optimistically-added user message and restore it to input
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last.role === 'user') {
              setInput(last.content);
              return prev.slice(0, -1);
            }
            return prev;
          });
          setError(ERROR_MESSAGE);
        },
      },
    });

  // Start session on mount
  useEffect(() => {
    createSession({ chapterId });
  }, [createSession, chapterId]);

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

  const hasSessionError = !!(error && !sessionId);

  return (
    <>
      <SessionError
        error={error}
        hasSession={sessionId !== null}
        isCreating={isCreating}
        onRetry={handleRetryCreate}
      />
      <ChatMessageList messages={messages} isLoading={isSending} error={error} />
      <ChatInput
        value={input}
        onChange={setInput}
        onSend={handleSend}
        disabled={isSending || isCreating || hasSessionError}
        sendDisabled={!input.trim() || isSending || isCreating}
      />
    </>
  );
};

import {
  useCreateChatSessionApiV1ChaptersChapterIdChatSessionsPost,
  useCreateQuizSessionApiV1ChaptersChapterIdQuizSessionsPost,
  useSendChatMessageApiV1ChatSessionsSessionIdMessagesPost,
  useSendQuizMessageApiV1QuizSessionsSessionIdMessagesPost,
} from '@/api/generated/chat/chat';

/**
 * A chat variant selects which backend endpoints back the {@link ChatDialog}. Quiz is
 * just a sub-type of chat, so both share the same request/response shapes and UI. The
 * `use*` hooks are structurally identical across variants (see generated chat API).
 */
export interface ChatVariant {
  title: (chapterName: string) => string;
  useCreateSession: typeof useCreateChatSessionApiV1ChaptersChapterIdChatSessionsPost;
  useSendMessage: typeof useSendChatMessageApiV1ChatSessionsSessionIdMessagesPost;
}

export const CHAT_VARIANT: ChatVariant = {
  title: (chapterName) => `Chat: ${chapterName}`,
  useCreateSession: useCreateChatSessionApiV1ChaptersChapterIdChatSessionsPost,
  useSendMessage: useSendChatMessageApiV1ChatSessionsSessionIdMessagesPost,
};

export const QUIZ_VARIANT: ChatVariant = {
  title: (chapterName) => `Quiz: ${chapterName}`,
  useCreateSession: useCreateQuizSessionApiV1ChaptersChapterIdQuizSessionsPost,
  useSendMessage: useSendQuizMessageApiV1QuizSessionsSessionIdMessagesPost,
};

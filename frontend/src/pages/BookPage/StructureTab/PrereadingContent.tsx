import type { ChapterPrereadingResponse } from '@/api/generated/model';
import { markdownStyles } from '@/theme/theme';
import { Box, CircularProgress, Typography, styled } from '@mui/material';
import ReactMarkdown from 'react-markdown';

interface PrereadingContentProps {
  content?: ChapterPrereadingResponse | null;
  isGenerating: boolean;
}

const MarkdownList = styled('ul')(({ theme }) => ({
  ...markdownStyles(theme),
  margin: 0,
  paddingLeft: '1.5em',
  '& li': {
    marginBottom: '0.5em',
  },
}));

export const PrereadingContent = ({ content, isGenerating }: PrereadingContentProps) => {
  if (isGenerating) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <CircularProgress size={24} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Generating pre-reading overview...
        </Typography>
      </Box>
    );
  }

  if (!content) {
    return null;
  }

  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="body1" sx={{ mb: 2.5 }}>
        {content.summary}
      </Typography>

      <Typography variant="body1" sx={{ mb: 1.5, fontWeight: 600 }}>
        Key Points:
      </Typography>
      <MarkdownList>
        {content.keypoints.map((point, idx) => (
          <li key={idx}>
            <ReactMarkdown>{point}</ReactMarkdown>
          </li>
        ))}
      </MarkdownList>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 3 }}>
        Generated on {new Date(content.generated_at).toLocaleDateString()}
      </Typography>
    </Box>
  );
};

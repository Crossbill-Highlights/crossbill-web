import type { PositionResponse } from '@/api/generated/model';
import { theme } from '@/theme/theme';
import { Box } from '@mui/material';
import type { ReactNode, RefObject } from 'react';
import { useEffect, useRef, useState } from 'react';

interface ChapterMarker {
  top: number;
  isRead: boolean;
}

interface ProgressLineState {
  lineStart: number;
  lineEnd: number;
  progressHeight: number;
  markers: ChapterMarker[];
}

function useProgressLine(
  containerRef: RefObject<HTMLElement | null>,
  readingPosition: PositionResponse | null | undefined
): ProgressLineState {
  const [state, setState] = useState<ProgressLineState>({
    lineStart: 0,
    lineEnd: 0,
    progressHeight: 0,
    markers: [],
  });

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !readingPosition) return;

    const isVisible = (el: HTMLElement): boolean => {
      let current = el.parentElement;
      while (current && current !== container) {
        // Detect collapsed (clientHeight 0) or collapsing (MUI exit transition)
        if (current.scrollHeight > 0 && current.clientHeight === 0) return false;
        if (
          current.classList.contains('MuiCollapse-root') &&
          !current.classList.contains('MuiCollapse-entered')
        )
          return false;
        current = current.parentElement;
      }
      return true;
    };

    const measure = () => {
      const allChapterEls = container.querySelectorAll('[data-chapter-read]');
      const containerRect = container.getBoundingClientRect();

      const markers: ChapterMarker[] = [];
      let progressHeight = 0;

      for (const el of allChapterEls) {
        const htmlEl = el as HTMLElement;
        if (!isVisible(htmlEl)) continue;

        const rect = htmlEl.getBoundingClientRect();
        const top = rect.top + 24 - containerRect.top;
        const isRead = el.getAttribute('data-chapter-read') === 'true';
        markers.push({ top, isRead });

        if (isRead) progressHeight = top;
      }

      const lineStart = markers.length > 0 ? markers[0].top : 0;
      const lineEnd = markers.length > 0 ? markers[markers.length - 1].top : 0;

      setState({ lineStart, lineEnd, progressHeight, markers });
    };

    const observer = new ResizeObserver(measure);
    observer.observe(container);

    // Re-measure when MUI Collapse class changes (e.g. MuiCollapse-entered added).
    // transitionend fires before React commits the class update, so we use
    // MutationObserver which fires after the DOM mutation.
    const classObserver = new MutationObserver((mutations) => {
      const collapseChanged = mutations.some(
        (m) => m.target instanceof HTMLElement && m.target.classList.contains('MuiCollapse-root')
      );
      if (collapseChanged) measure();
    });
    classObserver.observe(container, {
      attributes: true,
      subtree: true,
      attributeFilter: ['class'],
    });

    return () => {
      observer.disconnect();
      classObserver.disconnect();
    };
  }, [containerRef, readingPosition]);

  return readingPosition ? state : { lineStart: 0, lineEnd: 0, progressHeight: 0, markers: [] };
}

interface ReadingProgressLineProps {
  readingPosition: PositionResponse | null | undefined;
  children: ReactNode;
}

export const ReadingProgressLine = ({ readingPosition, children }: ReadingProgressLineProps) => {
  const containerRef = useRef<HTMLElement>(null);
  const { lineStart, lineEnd, progressHeight } = useProgressLine(containerRef, readingPosition);

  return (
    <Box ref={containerRef} sx={{ position: 'relative', pl: readingPosition ? '15px' : 0 }}>
      {readingPosition && (
        <>
          {/* Gray line from first to last marker */}
          <Box
            sx={{
              position: 'absolute',
              left: 0,
              top: lineStart,
              height: lineEnd - lineStart,
              borderRadius: '8px',
              width: 8,
              bgcolor: 'divider',
              transition: 'top 200ms ease-out, height 200ms ease-out',
            }}
          />
          {/* Brown progress overlay */}
          <Box
            sx={{
              position: 'absolute',
              left: 0,
              top: lineStart,
              width: 8,
              height: progressHeight - lineStart + 4,
              borderRadius: '8px',
              bgcolor: theme.palette.secondary.dark,
              transition: 'top 200ms ease-out, height 200ms ease-out',
            }}
          />
        </>
      )}
      {children}
    </Box>
  );
};

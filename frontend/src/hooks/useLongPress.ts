import { useCallback, useRef } from 'react';

export interface LongPressCoords {
  x: number;
  y: number;
}

interface UseLongPressOptions {
  delay?: number;
  moveThreshold?: number;
}

export const useLongPress = (
  onLongPress: (coords: LongPressCoords) => void,
  { delay = 500, moveThreshold = 10 }: UseLongPressOptions = {}
) => {
  const timerRef = useRef<number | null>(null);
  const startPos = useRef<LongPressCoords | null>(null);
  const firedRef = useRef(false);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    startPos.current = null;
  }, []);

  const onTouchStart = useCallback(
    (e: React.TouchEvent) => {
      if (e.touches.length !== 1) return;
      const { clientX, clientY } = e.touches[0];
      startPos.current = { x: clientX, y: clientY };
      firedRef.current = false;
      timerRef.current = window.setTimeout(() => {
        firedRef.current = true;
        if (startPos.current) onLongPress(startPos.current);
        clearTimer();
      }, delay);
    },
    [onLongPress, delay, clearTimer]
  );

  const onTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (!startPos.current) return;
      const { clientX, clientY } = e.touches[0];
      const dx = Math.abs(clientX - startPos.current.x);
      const dy = Math.abs(clientY - startPos.current.y);
      if (dx > moveThreshold || dy > moveThreshold) clearTimer();
    },
    [moveThreshold, clearTimer]
  );

  const onTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      // Suppress the synthetic click that follows a fired long-press; it is
      // hit-tested after any menu/backdrop opened by the press has rendered.
      if (firedRef.current) e.preventDefault();
      clearTimer();
    },
    [clearTimer]
  );

  const consumeClick = useCallback(() => {
    if (firedRef.current) {
      firedRef.current = false;
      return true;
    }
    return false;
  }, []);

  return {
    handlers: {
      onTouchStart,
      onTouchMove,
      onTouchEnd,
      onTouchCancel: clearTimer,
    },
    consumeClick,
  };
};

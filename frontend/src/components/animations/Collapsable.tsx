import { AnimatePresence, motion } from 'motion/react';
import { ReactNode } from 'react';

interface CollapsableProps {
  children: ReactNode;
  isExpanded: boolean;
}

export const Collapsable = ({ children, isExpanded }: CollapsableProps) => {
  return (
    <>
      <AnimatePresence initial={false}>
        {isExpanded ? (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            style={{
              overflow: 'hidden',
              flex: '1 1 auto',
              minHeight: 0,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {children}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
};

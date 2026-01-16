import { motion } from 'motion/react';

export const FadeInOut = ({ children, ekey }: { children: React.ReactNode; ekey: React.Key }) => {
  return (
    <motion.div
      key={ekey}
      initial={{
        opacity: 0,
        y: 20,
      }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
};

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence, Variants } from "motion/react";
import { cn } from "./Button";

interface HyperTextProps {
  text: string;
  duration?: number;
  framerProps?: Variants;
  className?: string;
  animateOnLoad?: boolean;
  characterSet?: string;
}

export function HyperText({
  text,
  duration = 800,
  framerProps = {
    initial: { opacity: 0, y: -10 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 3 },
  },
  className,
  animateOnLoad = true,
  characterSet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
}: HyperTextProps) {
  const [displayText, setDisplayText] = useState(text.split(""));
  const [isAnimating, setIsAnimating] = useState(false);
  const iterations = useRef(0);
  const isFirstRender = useRef(true);

  const triggerAnimation = () => {
    iterations.current = 0;
    setIsAnimating(true);
  };

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      if (animateOnLoad) {
        triggerAnimation();
      }
      return;
    }
    setDisplayText(text.split(""));
    triggerAnimation();
  }, [text, animateOnLoad]);

  useEffect(() => {
    if (!isAnimating) return;

    const maxIterations = text.length;
    const intervalDuration = duration / (maxIterations * 10);
    const interval = setInterval(() => {
      if (iterations.current < maxIterations) {
        setDisplayText((currentText) =>
          text.split("").map((l, i) =>
            l === " "
              ? l
              : i <= iterations.current
                ? text[i]
                : characterSet[Math.floor(Math.random() * characterSet.length)]
          )
        );
        iterations.current = iterations.current + 0.1;
      } else {
        setDisplayText(text.split(""));
        setIsAnimating(false);
        clearInterval(interval);
      }
    }, intervalDuration);

    return () => clearInterval(interval);
  }, [isAnimating, text, duration, characterSet]);

  return (
    <div
      className={cn("inline-flex overflow-hidden", className)}
      onMouseEnter={triggerAnimation}
    >
      <AnimatePresence mode="popLayout">
        {displayText.map((letter, i) => (
          <motion.span
            key={i}
            className={cn("", letter === " " ? "w-[0.5em]" : "")}
            variants={framerProps}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            {letter}
          </motion.span>
        ))}
      </AnimatePresence>
    </div>
  );
}

import { useState } from 'react';

interface Props {
  term: string;
  definition: string;
  children: React.ReactNode;
}

// NFR-4.1: financial terms (volatility, diversification, P/E ratio, etc.)
// get a beginner-friendly contextual definition on hover/tap.
export default function Tooltip({ term, definition, children }: Props) {
  const [visible, setVisible] = useState(false);

  return (
    <span
      className="relative underline decoration-dotted cursor-help"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onClick={() => setVisible((v) => !v)}
      aria-label={`${term}: ${definition}`}
    >
      {children}
      {visible && (
        <span className="absolute bottom-full mb-1 left-0 w-48 text-xs bg-black text-white rounded p-2 z-10">
          {definition}
        </span>
      )}
    </span>
  );
}

"use client";

interface CodeBlockProps {
  title: string;
  language: string;
  children: string;
}

export function CodeBlock({ title, language, children }: CodeBlockProps) {
  return (
    <div className="glass-dark overflow-hidden rounded-2xl">
      <div className="flex items-center justify-between border-b border-white/5 px-4 py-2.5">
        <p className="text-xs font-medium text-gray-300">{title}</p>
        <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] text-gray-400">
          {language}
        </span>
      </div>
      <pre className="overflow-x-auto p-4 text-xs leading-relaxed text-gray-300 font-mono">
        <code>{children}</code>
      </pre>
    </div>
  );
}

'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CollapsibleSectionProps {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
  className?: string;
  headerClassName?: string;
  accentColor?: 'indigo' | 'slate' | 'blue' | 'emerald';
}

export default function CollapsibleSection({
  title,
  icon,
  children,
  defaultOpen = true,
  className,
  headerClassName,
  accentColor = 'slate'
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const colorStyles = {
    indigo: {
      border: 'border-indigo-200',
      bg: 'bg-indigo-50',
      text: 'text-indigo-900',
      icon: 'text-indigo-600'
    },
    slate: {
      border: 'border-slate-200',
      bg: 'bg-slate-50',
      text: 'text-slate-900',
      icon: 'text-slate-600'
    },
    blue: {
      border: 'border-blue-200',
      bg: 'bg-blue-50',
      text: 'text-blue-900',
      icon: 'text-blue-600'
    },
    emerald: {
      border: 'border-emerald-200',
      bg: 'bg-emerald-50',
      text: 'text-emerald-900',
      icon: 'text-emerald-600'
    }
  };

  const styles = colorStyles[accentColor];

  return (
    <div className={cn("border rounded-xl overflow-hidden transition-all duration-200", styles.border, className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "w-full flex items-center justify-between px-4 py-3 transition-colors",
          styles.bg,
          headerClassName
        )}
      >
        <div className="flex items-center gap-3">
          {icon && <span className={styles.icon}>{icon}</span>}
          <h3 className={cn("font-semibold text-sm uppercase tracking-wide", styles.text)}>
            {title}
          </h3>
        </div>
        <div className={styles.icon}>
          {isOpen ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
        </div>
      </button>
      
      <div
        className={cn(
          "transition-all duration-300 ease-in-out overflow-hidden",
          isOpen ? "max-h-[5000px] opacity-100" : "max-h-0 opacity-0"
        )}
      >
        <div className="p-4 bg-white/50">
          {children}
        </div>
      </div>
    </div>
  );
}

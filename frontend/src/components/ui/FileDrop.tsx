"use client";

import { FileText, Upload, X } from "lucide-react";
import { useState, type DragEvent } from "react";
import { cn, formatBytes } from "@/lib/utils";

interface FileDropProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  /** Value for the input's `accept` attribute, e.g. `.pdf`. */
  accept: string;
  title: string;
  hint: string;
  removeLabel: string;
}

/** A single-file picker that accepts both clicks and drag-and-drop. */
export function FileDrop({ file, onFileChange, accept, title, hint, removeLabel }: FileDropProps) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragging(false);
    onFileChange(event.dataTransfer.files[0] ?? null);
  };

  if (file) {
    return (
      <div className="flex items-center gap-3 rounded-md border border-line-strong bg-surface px-4 py-3">
        <FileText className="h-5 w-5 shrink-0 text-brand" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">
            <bdi>{file.name}</bdi>
          </p>
          <p className="text-sm text-muted tabular">
            <bdi>{formatBytes(file.size)}</bdi>
          </p>
        </div>
        <button
          type="button"
          onClick={() => onFileChange(null)}
          className="flex h-8 w-8 items-center justify-center rounded-md text-muted hover:bg-subtle hover:text-ink"
          aria-label={removeLabel}
        >
          <X className="h-4 w-4" aria-hidden />
        </button>
      </div>
    );
  }

  return (
    <label
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={cn(
        "flex cursor-pointer flex-col items-center gap-3 rounded-md border border-dashed px-6 py-10 text-center transition-colors",
        "has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-brand",
        dragging ? "border-brand bg-brand-soft" : "border-line-strong bg-surface hover:border-faint",
      )}
    >
      <input
        type="file"
        accept={accept}
        className="sr-only"
        onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
      />
      <Upload className="h-6 w-6 text-muted" aria-hidden />
      <span className="space-y-1">
        <span className="block font-medium">{title}</span>
        <span className="block text-sm text-muted">{hint}</span>
      </span>
    </label>
  );
}

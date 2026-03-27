import { useEffect, useRef, useState, useCallback } from "react";

interface WatchedModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (note: string) => void;
  isLoading: boolean;
}

const MAX_NOTE_LENGTH = 500;

export default function WatchedModal({
  isOpen,
  onClose,
  onConfirm,
  isLoading,
}: WatchedModalProps) {
  const [note, setNote] = useState<string>("");
  const overlayRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const cancelBtnRef = useRef<HTMLButtonElement>(null);
  const confirmBtnRef = useRef<HTMLButtonElement>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }

      if (e.key === "Tab") {
        const elements: Array<HTMLTextAreaElement | HTMLButtonElement | null> = [
          textareaRef.current,
          confirmBtnRef.current,
          cancelBtnRef.current,
        ];
        const focusable: Array<HTMLTextAreaElement | HTMLButtonElement> = [];
        for (const el of elements) {
          if (el !== null) focusable.push(el);
        }
        if (focusable.length === 0) return;

        const first: HTMLTextAreaElement | HTMLButtonElement = focusable[0];
        const last: HTMLTextAreaElement | HTMLButtonElement = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      setNote("");
      document.addEventListener("keydown", handleKeyDown);
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 0);
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  function handleOverlayClick(e: React.MouseEvent<HTMLDivElement>): void {
    if (e.target === overlayRef.current) {
      onClose();
    }
  }

  function handleNoteChange(e: React.ChangeEvent<HTMLTextAreaElement>): void {
    const value = e.target.value;
    if (value.length <= MAX_NOTE_LENGTH) {
      setNote(value);
    }
  }

  function handleConfirm(): void {
    onConfirm(note.trim());
  }

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Marcar película como vista"
    >
      <div className="mx-4 w-full max-w-md rounded-xl bg-gray-900 p-6 shadow-2xl">
        <h2 className="mb-4 text-lg font-bold text-white">Marcar como vista</h2>

        <label className="mb-1 block text-sm text-gray-400" htmlFor="watched-note">
          Nota inicial (opcional)
        </label>
        <textarea
          id="watched-note"
          ref={textareaRef}
          value={note}
          onChange={handleNoteChange}
          placeholder="¿Qué te pareció esta película?"
          rows={4}
          maxLength={MAX_NOTE_LENGTH}
          className="w-full resize-none rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
        />
        <p className="mb-4 text-right text-xs text-gray-500">
          {note.length}/{MAX_NOTE_LENGTH.toString()}
        </p>

        <div className="flex items-center justify-end gap-3">
          <button
            ref={cancelBtnRef}
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="rounded-lg px-4 py-2 text-sm font-medium text-gray-400 transition hover:text-white"
          >
            Cancelar
          </button>
          <button
            ref={confirmBtnRef}
            type="button"
            onClick={handleConfirm}
            disabled={isLoading}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? "Guardando…" : "Marcar como vista"}
          </button>
        </div>
      </div>
    </div>
  );
}

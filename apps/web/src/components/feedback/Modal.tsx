import { useEffect } from "react";
import type { ReactNode } from "react";
import { cn } from "../../lib/cn";
import { Icon } from "../ui/Icon";

type ModalSize = "sm" | "md" | "lg";

type ModalProps = {
  open: boolean;
  title: string;
  description?: string;
  size?: ModalSize;
  children: ReactNode;
  footer?: ReactNode;
  onClose: () => void;
};

const sizeClasses: Record<ModalSize, string> = {
  sm: "max-w-[30rem]",
  md: "max-w-[45rem]",
  lg: "max-w-[60rem]"
};

export function Modal({
  open,
  title,
  description,
  size = "md",
  children,
  footer,
  onClose
}: ModalProps) {
  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleEscape);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener("keydown", handleEscape);
    };
  }, [onClose, open]);

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-surface-overlay/80 p-4 backdrop-blur-sm"
      role="presentation"
      onClick={onClose}
    >
      <div
        aria-modal="true"
        role="dialog"
        className={cn(
          "w-full rounded-shell border border-border-subtle bg-surface-panel shadow-modal",
          sizeClasses[size]
        )}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-border-subtle px-panel py-5">
          <div className="space-y-2">
            <h2 className="type-heading-md">{title}</h2>
            {description ? <p className="type-body-sm">{description}</p> : null}
          </div>
          <button
            type="button"
            className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-field border border-border-subtle bg-surface-subtle/70 text-content-secondary transition hover:text-content-primary"
            onClick={onClose}
            aria-label="Close dialog"
          >
            <Icon name="close" className="h-4 w-4" />
          </button>
        </div>
        <div className="px-panel py-5">{children}</div>
        {footer ? (
          <div className="border-t border-border-subtle px-panel py-4">{footer}</div>
        ) : null}
      </div>
    </div>
  );
}

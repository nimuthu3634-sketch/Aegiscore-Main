import type { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  meta?: ReactNode;
  actions?: ReactNode;
};

export function PageHeader({
  eyebrow,
  title,
  description,
  meta,
  actions
}: PageHeaderProps) {
  return (
    <div className="panel-subtle flex flex-col gap-5 p-panel xl:flex-row xl:items-end xl:justify-between">
      <div className="space-y-3">
        {eyebrow ? <p className="type-label-md">{eyebrow}</p> : null}
        <div className="space-y-2.5">
          <h2 className="type-display-md">{title}</h2>
          {description ? <p className="max-w-3xl type-body-md text-content-secondary">{description}</p> : null}
        </div>
        {meta}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
    </div>
  );
}

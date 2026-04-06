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
    <div className="panel-subtle flex flex-col gap-4 p-panel xl:flex-row xl:items-end xl:justify-between">
      <div className="space-y-2.5">
        {eyebrow ? <p className="type-label-sm text-content-muted">{eyebrow}</p> : null}
        <div className="space-y-2">
          <h2 className="text-[1.6rem] font-semibold leading-tight text-content-primary">{title}</h2>
          {description ? <p className="max-w-3xl type-body-md text-content-secondary">{description}</p> : null}
        </div>
        {meta}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
    </div>
  );
}

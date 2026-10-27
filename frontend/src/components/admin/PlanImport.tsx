"use client";

import { Download } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button, Field, FileDrop, Notice, Select, TextInput, buttonStyles } from "@/components/ui";
import { useDepartments } from "@/hooks/useDepartments";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { importStudyPlan, studyPlanWorkbookUrl } from "@/lib/api";
import { localize } from "@/lib/utils";
import type { PlanImportResult, PlanIssue } from "@/types";

function SectionTitle({ step, children }: { step: number; children: React.ReactNode }) {
  return (
    <h2 className="flex items-baseline gap-3 border-b border-line-strong pb-2 font-semibold">
      <span className="text-sm font-medium text-brand tabular">{step}</span>
      {children}
    </h2>
  );
}

function IssueList({ issues }: { issues: PlanIssue[] }) {
  const t = useTranslations("Admin");

  return (
    <div className="space-y-2">
      <p className="font-medium text-danger">{t("issuesTitle", { count: issues.length })}</p>
      <ul className="divide-y divide-line border-y border-line">
        {issues.map((issue, index) => (
          <li key={index} className="grid gap-1 py-3 sm:grid-cols-[10rem_1fr] sm:gap-4">
            <span className="text-sm text-muted tabular">
              {issue.row !== null
                ? t("location", { sheet: issue.sheet ?? "", row: issue.row })
                : (issue.sheet ?? "")}
            </span>
            <span className="text-sm">
              {t(`issues.${issue.code}`, {
                sheet: issue.sheet ?? "",
                field: issue.field ?? "",
                value: issue.value ?? "",
              })}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Staff tool: download a plan as Excel, edit it, check the upload, then publish it. */
export function PlanImport() {
  const t = useTranslations("Admin");
  const locale = useLocale();
  const describeError = useErrorMessage();
  const departments = useDepartments();

  const [token, setToken] = useState("");
  const [download, setDownload] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<PlanImportResult | null>(null);
  const [busy, setBusy] = useState<"check" | "publish" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const downloadCode = download ?? departments.data?.[0]?.code ?? null;

  const chooseFile = (next: File | null) => {
    setFile(next);
    setResult(null);
    setError(null);
  };

  const submit = async (publish: boolean) => {
    setError(null);
    if (!token) return setError(t("needToken"));
    if (!file) return setError(t("needFile"));

    setBusy(publish ? "publish" : "check");
    try {
      setResult(await importStudyPlan(file, token, publish));
    } catch (caught) {
      setError(describeError(caught));
    } finally {
      setBusy(null);
    }
  };

  const summary = result?.summary;
  const canPublish = summary && result.issues.length === 0 && !result.published;

  return (
    <div className="space-y-12">
      <section className="space-y-4">
        <SectionTitle step={1}>{t("tokenTitle")}</SectionTitle>
        <Field id="admin-token" label={t("tokenLabel")} hint={t("tokenHint")}>
          <TextInput
            id="admin-token"
            type="password"
            autoComplete="off"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            className="sm:max-w-sm"
            dir="ltr"
          />
        </Field>
      </section>

      <section className="space-y-4">
        <SectionTitle step={2}>{t("downloadTitle")}</SectionTitle>
        <p className="text-muted">{t("downloadHint")}</p>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <Field id="download-department" label={t("department")}>
            <Select
              id="download-department"
              value={downloadCode ?? ""}
              onChange={(event) => setDownload(event.target.value)}
              className="sm:w-72"
            >
              {departments.data?.map((item) => (
                <option key={item.code} value={item.code}>
                  {localize(item.name, locale)}
                </option>
              ))}
            </Select>
          </Field>
          {downloadCode && (
            <a href={studyPlanWorkbookUrl(downloadCode)} download className={buttonStyles({ variant: "secondary" })}>
              <Download className="h-4 w-4" aria-hidden />
              {t("downloadButton")}
            </a>
          )}
        </div>
      </section>

      <section className="space-y-4">
        <SectionTitle step={3}>{t("uploadTitle")}</SectionTitle>
        <FileDrop
          file={file}
          onFileChange={chooseFile}
          accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          title={t("dropTitle")}
          hint={t("dropHint")}
          removeLabel={t("remove")}
        />

        {error && <Notice tone="error">{error}</Notice>}

        {result && result.issues.length > 0 && <IssueList issues={result.issues} />}

        {summary && (
          <Notice tone={result.published ? "success" : "info"}>
            <p className="font-medium text-ink">
              {result.published
                ? t("published", { name: localize(summary.name, locale) })
                : t("valid", { name: localize(summary.name, locale) })}
            </p>
            <p className="tabular">
              {t("summary", {
                courses: summary.course_count,
                levels: summary.level_count,
                hours: summary.total_hours,
              })}
            </p>
            {canPublish && <p>{t("replaceWarning", { code: summary.code })}</p>}
          </Notice>
        )}

        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" onClick={() => submit(false)} loading={busy === "check"} disabled={busy !== null}>
            {t("check")}
          </Button>
          {canPublish && (
            <Button onClick={() => submit(true)} loading={busy === "publish"} disabled={busy !== null}>
              {t("publish")}
            </Button>
          )}
        </div>
      </section>
    </div>
  );
}

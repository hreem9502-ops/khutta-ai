"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState, type FormEvent } from "react";
import { Button, Field, FileDrop, Notice, Select } from "@/components/ui";
import { useDepartments } from "@/hooks/useDepartments";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { usePlanner } from "@/hooks/usePlanner";
import { useRouter } from "@/i18n/routing";
import { parseTranscript } from "@/lib/api";
import { MAX_UPLOAD_BYTES, TERMS } from "@/lib/constants";
import { localize } from "@/lib/utils";
import type { Term } from "@/types";

/** First step: choose department and term, then upload and read the transcript. */
export function UploadForm() {
  const t = useTranslations("Upload");
  const tTerms = useTranslations("Terms");
  const tErrors = useTranslations("Errors");
  const locale = useLocale();
  const router = useRouter();
  const { start } = usePlanner();
  const describeError = useErrorMessage();
  const departments = useDepartments();

  const [department, setDepartment] = useState("");
  const [term, setTerm] = useState<Term | "">("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const chooseFile = (candidate: File | null) => {
    setError(null);
    const isPdf = candidate?.type === "application/pdf" || candidate?.name.toLowerCase().endsWith(".pdf");
    if (candidate && !isPdf) {
      setError(tErrors("notPdf"));
      return;
    }
    if (candidate && candidate.size > MAX_UPLOAD_BYTES) {
      setError(tErrors("file_too_large"));
      return;
    }
    setFile(candidate);
  };

  const fail = (message: string): null => {
    setError(message);
    return null;
  };

  /** Returns the chosen department and term, or records why they are incomplete. */
  const requireSelection = (): { department: string; term: Term } | null => {
    if (!department) return fail(t("needDepartment"));
    if (!term) return fail(t("needTerm"));
    return { department, term };
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    const selection = requireSelection();
    if (!selection) return;
    if (!file) {
      fail(t("needFile"));
      return;
    }

    setSubmitting(true);
    try {
      const parsed = await parseTranscript(file, selection.department);
      start({ ...selection, courses: parsed.courses, gpa: parsed.gpa, reader: parsed.reader });
      router.push("/review");
    } catch (caught) {
      setError(describeError(caught));
      setSubmitting(false);
    }
  };

  const handleManual = () => {
    setError(null);
    const selection = requireSelection();
    if (!selection) return;
    start({ ...selection, courses: [], gpa: null, reader: null });
    router.push("/review");
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6" noValidate>
      <div className="grid gap-6 sm:grid-cols-2">
        <Field id="department" label={t("department")}>
          <Select
            id="department"
            value={department}
            onChange={(event) => setDepartment(event.target.value)}
            disabled={!departments.data}
          >
            <option value="" disabled>
              {t("selectDepartment")}
            </option>
            {departments.data?.map((item) => (
              <option key={item.code} value={item.code}>
                {localize(item.name, locale)}
              </option>
            ))}
          </Select>
        </Field>
        <Field id="term" label={t("term")}>
          <Select id="term" value={term} onChange={(event) => setTerm(event.target.value as Term)}>
            <option value="" disabled>
              {t("selectTerm")}
            </option>
            {TERMS.map((value) => (
              <option key={value} value={value}>
                {tTerms(value)}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      {departments.error !== undefined && <Notice tone="error">{t("departmentsFailed")}</Notice>}

      <FileDrop
        file={file}
        onFileChange={chooseFile}
        accept="application/pdf,.pdf"
        title={t("dropTitle")}
        hint={t("dropHint")}
        removeLabel={t("remove")}
      />

      {error && <Notice tone="error">{error}</Notice>}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Button type="submit" size="lg" loading={submitting}>
          {submitting ? t("submitting") : t("submit")}
        </Button>
        <Button type="button" variant="ghost" onClick={handleManual} disabled={submitting}>
          {t("manual")}
        </Button>
      </div>

      <p className="text-sm text-muted">{t("privacy")}</p>
    </form>
  );
}

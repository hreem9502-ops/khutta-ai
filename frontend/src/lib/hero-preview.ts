import type { LocalizedText } from "@/types";

/** Illustrative rows for the landing-page preview. Not served by the API. */
export const HERO_PREVIEW_COURSES: {
  code: string;
  name: LocalizedText;
  hours: number;
  note: LocalizedText;
}[] = [
  {
    code: "CS 201",
    name: { ar: "برمجة 2", en: "Programming 2" },
    hours: 4,
    note: { ar: "تكملة لبرمجة 1 التي اجتزتها بتقدير جيد", en: "Follows Programming 1, passed with a B" },
  },
  {
    code: "CS 202",
    name: { ar: "الرياضيات المتقطعة", en: "Discrete Structures" },
    hours: 3,
    note: { ar: "متطلب سابق لهياكل البيانات والخوارزميات", en: "Prerequisite for Data Structures and Algorithms" },
  },
  {
    code: "MATH 201",
    name: { ar: "الجبر الخطي", en: "Linear Algebra" },
    hours: 3,
    note: { ar: "تكملة للتفاضل والتكامل", en: "Continues Calculus" },
  },
  {
    code: "ENG 102",
    name: { ar: "لغة إنجليزية 2", en: "English 2" },
    hours: 3,
    note: { ar: "تخفف الحمل التقني في هذا الفصل", en: "Lightens the technical load this term" },
  },
];

export const HERO_PREVIEW_MAX_HOURS = 18;

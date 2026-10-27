"""Static vocabulary shared by the parsing and recommendation services."""

# --- Grades -----------------------------------------------------------------
# Tokens are compared after ``normalize_token`` (upper-cased, Arabic-normalised).

PASSING_GRADES: frozenset[str] = frozenset(
    {"A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "P","ممتاز", "جيد جدا", "جيد", "مقبول", "ناجح"}
)
FAILING_GRADES: frozenset[str] = frozenset({"F", "FA", "DN", "راسب", "ل", "محروم"})
IN_PROGRESS_GRADES: frozenset[str] = frozenset({"IP", "INP", "جاري", "قيد الدراسة", "مسجل"})
WITHDRAWN_GRADES: frozenset[str] = frozenset({"W", "WP", "WF", "منسحب", "انسحاب"})

ALL_GRADE_TOKENS: frozenset[str] = (
    PASSING_GRADES | FAILING_GRADES | IN_PROGRESS_GRADES | WITHDRAWN_GRADES
)

# --- Transcript text patterns -----------------------------------------------

# A course code is a short run of letters (Latin or Arabic) followed by a 3-4 digit number.
COURSE_CODE_PATTERN = r"[A-Za-zء-ي]{2,6}[\s\-]?\d{3,4}"
REVERSED_COURSE_CODE_PATTERN = r"\d{3,4}[\s\-]?[ء-ي]{2,6}"
GPA_LABEL_PATTERN = r"(?:cumulative\s*gpa|overall\s*gpa|gpa|المعدل\s*التراكمي|المعدل|يمكارتلا\s*لدعملا|لدعملا)"
GPA_VALUE_PATTERN = r"\b([0-5](?:\.\d{1,3})?)\b"

# --- AI-assisted transcript reading -------------------------------------------

# The AI reader is tried when the rule-based reader finds fewer courses than this...
MIN_RULE_READ_COURSES = 3
# ...or when fewer than this share of the courses it found have a recognised grade.
MIN_GRADED_SHARE = 0.5
# Upper bound on transcript lines sent to the model.
MAX_AI_TRANSCRIPT_LINES = 200

# --- Recommendation tuning --------------------------------------------------

# A course that unlocks at least this many others is flagged as a bottleneck.
BOTTLENECK_UNLOCK_THRESHOLD = 2
# Upper bound on how many unmet-prerequisite courses are returned for display.
MAX_BLOCKED_COURSES = 12

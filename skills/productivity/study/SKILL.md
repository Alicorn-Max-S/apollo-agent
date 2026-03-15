---
name: study
description: Interactive study sessions with document upload, 10 quiz formats, performance tracking, semantic-search-powered spaced repetition, and smart suggestions.
version: 1.0.0
author: community
license: MIT
metadata:
  hermes:
    tags: [Study, Quiz, Flashcards, Practice, Education, Spaced Repetition, School]
    related_skills: [file-analysis, canvas, todoist, document-analysis, text-analysis]
---

# Study — Interactive Study Sessions & Performance Tracking

Upload study materials, get quizzed with 10 different question formats, track what you know vs. struggle with, and get smart suggestions on what to study next. Uses spaced repetition with semantic search to avoid repeating the same questions.

**IMPORTANT**: All tool references (`read_file`, `vision_analyze`, `clarify`, `terminal`, `memory`, `skill_view`) are **agent tools** — invoke them as tool calls, NOT as Python imports.

## Scripts

```bash
STUDY="python ~/.hermes/skills/productivity/study/scripts/study_db.py"
```

## Available Commands

```bash
# Classes (top-level organization, e.g., "Spanish 3", "AP US History")
$STUDY list_classes
$STUDY create_class "Spanish 3"

# Categories (within a class, e.g., "pretérito", "imperfecto", "Civil War")
$STUDY list_categories --class "Spanish 3"
$STUDY create_category --class "Spanish 3" --name "pretérito"

# Study files
$STUDY save_file --class "Spanish 3" --category "pretérito" --filename "verbs.pdf" --content - --content-type "verb_list"
$STUDY list_files [--class "Spanish 3"]
$STUDY get_file FILE_ID
$STUDY delete_file FILE_ID
$STUDY update_last_studied FILE_ID

# Record a question result (auto-updates scores and type counts)
$STUDY record --class "Spanish 3" --category "pretérito" \
  --question "conjugate hablar (yo, pretérito)" \
  --correct-answer "hablé" --user-answer "hablé" \
  --is-correct 1 --type "conjugation"

# Semantic search (find similar past questions to avoid repetition)
$STUDY search_similar --class "Spanish 3" --category "pretérito" \
  --query "conjugate hablar yo pretérito" --limit 5

# Knowledge scores & history
$STUDY get_scores [--class "Spanish 3"]
$STUDY get_score --class "Spanish 3" --category "pretérito"
$STUDY get_history --class "Spanish 3" [--category "pretérito"] [--limit 20] [--incorrect-only]
$STUDY get_weak_areas --class "Spanish 3"
$STUDY update_summary --class "Spanish 3" --category "pretérito" --summary "..."

# Smart suggestions (what to study next)
$STUDY suggest
```

## 10 Question Types

| # | Type | Best For |
|---|------|----------|
| 1 | `fill_in_blank` | Vocabulary, grammar, formulas |
| 2 | `conjugation` | Language verb practice |
| 3 | `vocabulary` | Terms ↔ definitions, translations |
| 4 | `full_sentence` | History, literature, analysis |
| 5 | `multiple_choice` | Low-knowledge review, concept recognition |
| 6 | `true_false` | Quick concept checks, misconceptions |
| 7 | `short_answer` | Science, social studies, focused explanations |
| 8 | `matching` | Pairs: dates↔events, terms↔definitions |
| 9 | `ordering` | Timelines, process steps, sequences |
| 10 | `diagram_label` | Anatomy, geography, diagrams |

For detailed descriptions, answer formats, and checking rules for each type, load the reference: `skill_view("study")` and read `references/study_methods.md`.

---

## Starting a Study Session

When the user says "let's study" or similar **without specifying a topic**:

### Step 1: Gather Context

Run these commands to understand what the user should study:

```bash
# 1. Check study priorities (scores, staleness, never-studied categories)
$STUDY suggest

# 2. Check available study materials
$STUDY list_files
```

### Step 2: Check External Sources

Also check for upcoming deadlines and tasks:

- **Canvas assignments**: `skill_view("canvas")` → list pending assignments, especially those due within the next 3 days
- **Todoist tasks**: `skill_view("todoist")` → list tasks with "study" or "school" labels that are due soon

### Step 3: Present a Smart Suggestion

Combine all data into a single recommendation:

> "Based on your scores, you're weakest in **[category]** (scoring [X]/10). You also have a **[Canvas assignment]** due [date]. Here are your options:
> 1. Study **[weak category]** — you've been struggling with [specific area]
> 2. Prep for **[Canvas assignment]** — due [date]
> 3. Review **[stale topic]** — last studied [N] days ago
> 4. Something else
>
> What would you like to study?"

---

## Uploading Study Materials

When the user provides a file to study from:

### Step 1: Analyze the File

Use the file-analysis skill to detect file type and extract content:

```
skill_view("file-analysis")
```

Follow the file-analysis skill instructions to detect the file type and extract text content. For PDFs use document-analysis, for images use OCR, etc.

### Step 2: Identify Class & Category

Ask the user (or infer from content):
- **Class**: Which class does this belong to? (e.g., "Spanish 3", "AP Bio")
- **Category**: What specific topic? (e.g., "pretérito", "cell biology")
- **Content type**: What kind of material? (verb_list, notes, vocabulary, formulas, etc.)

If the class or category doesn't exist yet, create them:
```bash
$STUDY create_class "Spanish 3"
$STUDY create_category --class "Spanish 3" --name "pretérito"
```

### Step 3: Save the Material

Pipe the extracted content via stdin to avoid shell argument length limits:

```bash
echo 'EXTRACTED_CONTENT' | $STUDY save_file --class "Spanish 3" --category "pretérito" \
  --filename "original_filename.pdf" --content - --content-type "verb_list"
```

### Step 4: Confirm & Offer to Study

> "Saved **[filename]** to **[class] → [category]**. Would you like to start studying this material now?"

---

## Adaptive Difficulty Logic

**Before asking questions** for a class/category, check the user's knowledge level:

```bash
$STUDY get_scores --class "CLASS_NAME"
```

Then apply this logic:

### Score Not Found (New Topic)
- This is a brand new topic — **start quizzing immediately**
- No need to ask for confirmation
- Use the question type the user chose, or pick one appropriate for the content

### Score 0–3 (Struggling / Beginner)
- **Start quizzing immediately** — user needs practice
- Prefer easier formats: `multiple_choice`, `true_false`, `fill_in_blank`
- Give detailed explanations after each answer
- Include hints when appropriate ("Think about the -ar verb ending pattern...")

### Score 4–7 (Developing)
- **Check specifics before quizzing**:
  ```bash
  $STUDY get_history --class "CLASS_NAME" --category "CATEGORY" --incorrect-only --limit 10
  ```
- Review what the user got wrong — look for patterns (e.g., consistently wrong on irregular verbs)
- Focus questions on weak patterns, not things they already know well
- Use medium-difficulty formats: `fill_in_blank`, `short_answer`, `vocabulary`, `conjugation`

### Score 8–10 (Proficient)
- **Ask for confirmation before studying**:
  > "You're scoring **[score]/10** on **[category]**. You know this pretty well! Would you like to:
  > 1. Do a quick review to keep it fresh
  > 2. Focus on a specific sub-area (e.g., irregular stems in pretérito)
  > 3. Try a harder format (full sentence, no hints)
  > 4. Study something else instead"
- Only proceed if the user confirms
- Use harder formats: `full_sentence`, `conjugation` (without hints), `ordering`
- Consider suggesting a more specific sub-focus (e.g., "conjugation for pretérito with irregular stems where only the verb is given")

---

## Question Type Selection & Consistency

### CRITICAL RULE: Do NOT switch question types during a conversation unless the user explicitly asks to change.

### Selecting a Type

1. **If the user requests a specific type** → use that type for the ENTIRE session. No exceptions. No switching.

2. **If the user doesn't specify a type**, check the type distribution:
   ```bash
   $STUDY get_scores --class "CLASS_NAME"
   ```
   Look at `type_distribution` in the response. Pick a type that:
   - Is underrepresented in the distribution (for variety across sessions)
   - Actually works well for the content (see compatibility below)
   - Matches the difficulty tier (see Adaptive Difficulty above)

3. **Announce the type once** at the start:
   > "I'll quiz you with **[type]** questions on **[category]**. Let me know if you want to switch formats."

4. **Stick with this type** for the entire session until the user asks to change.

### Type-Content Compatibility

**Never force a type that doesn't fit the material.** Even if it's low in the distribution:

| Content Type | Good Question Types | Avoid |
|-------------|-------------------|-------|
| Verb lists | conjugation, fill_in_blank, multiple_choice | diagram_label, ordering |
| Vocabulary | vocabulary, fill_in_blank, matching, multiple_choice | conjugation, diagram_label |
| History notes | full_sentence, short_answer, ordering, true_false | conjugation, diagram_label |
| Science notes | short_answer, true_false, diagram_label, multiple_choice | conjugation |
| Math formulas | fill_in_blank, short_answer, ordering | conjugation, matching |
| Anatomy/diagrams | diagram_label, vocabulary, matching | conjugation, ordering |

---

## Quiz Flow

### One Question at a Time

1. **Generate a question** from the study material using the chosen question type
2. **Before asking**, check for similarity to past questions:
   ```bash
   $STUDY search_similar --class "CLASS" --category "CAT" --query "your candidate question" --limit 3
   ```
   If any result has similarity > 0.85, generate a different question to avoid repetition.
3. **Ask the question** and wait for the user's answer
4. **Check accuracy** using the Answer Checking Rules below
5. **Give immediate feedback**: explain why correct or incorrect, provide the correct answer if wrong
6. **Record the result**:
   ```bash
   $STUDY record --class "CLASS" --category "CAT" \
     --question "the question" --correct-answer "correct" \
     --user-answer "what user said" --is-correct 1 --type "conjugation"
   ```

### Spaced Repetition (Every Other Question)

Once there are **≥10 question records** for the current class:

- **Alternate**: new question → spaced rep → new question → spaced rep → ...
- For spaced rep questions:
  1. Get recent incorrect answers: `$STUDY get_history --class "CLASS" --incorrect-only --limit 10`
  2. Pick one incorrect item
  3. Generate a **similar but NOT identical** question on the same concept
     - Example: if user got "hablar yo pretérito" wrong → ask "comer yo pretérito" (same structure, different verb)
  4. Use `$STUDY search_similar` to verify the new question isn't too similar to one already asked
- If no incorrect items exist → just ask new questions (no forced spaced rep)

### Progress Updates

- After every **5 questions**, show a mini progress summary:
  > "Progress: **4/5 correct** so far. You're doing well with regular -ar verbs but missed the irregular stem for 'tener'."

- After the **session ends** (user says done, or after ~15-20 questions), generate and save a summary:
  ```bash
  $STUDY update_summary --class "CLASS" --category "CAT" \
    --summary "Strong with regular -ar/-er verbs in pretérito. Struggles with irregular stems (tener→tuv-, poner→pus-). Accent marks sometimes omitted."
  ```

---

## Answer Checking Rules

**CRITICAL: Evaluate answers semantically, NOT with exact string matching.** The goal is to assess whether the student knows the concept, not whether they typed it identically.

### Conjugation
- Accept with or without subject pronoun: "yo hablé" = "hablé" ✓
- Case-insensitive: "Hablé" = "hablé" ✓
- **Accent leniency**: "hable" for "hablé" → mark as **correct** but flag: "Correct! Note: don't forget the accent → habl**é**"
- Wrong tense or form → **incorrect**, explain the rule and give correct conjugation

### Vocabulary / One-Word
- Case-insensitive
- Accept common synonyms ("brief" = "short-lived" = "fleeting" for "ephemeral")
- Accept singular/plural variations with a note
- For translations, accept common alternative translations

### Fill in the Blank
- Only evaluate the **blank portion**, ignore surrounding text
- Apply same leniency as vocabulary
- Case-insensitive for non-proper nouns

### Math
- Evaluate mathematical equivalence: 1/2 = 0.5 = 50%
- Accept equivalent expression forms
- For multi-step problems, note which steps were correct if the final answer is wrong

### Full Sentence / Short Answer
- Check for **key concepts/facts** — keep a mental checklist of required points
- Don't penalize grammar or style differences
- Note if important details are missing but give partial credit
- Accept different valid explanations of the same concept

### True/False
- Accept: "true"/"false", "t"/"f", "yes"/"no"
- Evaluate the user's explanation/reasoning, not just the T/F choice
- If T/F is right but reasoning is wrong, note the issue

### Multiple Choice
- Accept letter (A/B/C/D, case-insensitive) or full option text

### Matching / Ordering
- Accept any clear format (numbered list, arrows, etc.)
- Evaluate each pair/position individually → partial credit
- Note which specific items were wrong

### Diagram Label
- Evaluate each label independently
- Accept common alternative names
- Case-insensitive, partial credit per label

### Always
- **Explain WHY** the answer is correct or incorrect
- For incorrect answers: provide the correct answer + a brief rule or explanation
- For accent issues: mark correct but remind about the accent

---

## Cross-Skill Integration

### File Analysis → Study Material

When you use `skill_view("file-analysis")` to analyze a document and it contains study-worthy content:

> "This looks like study material. Would you like me to save it for future study sessions?"

If yes, follow the Uploading Study Materials workflow above.

### Canvas → Study Suggestions

When checking Canvas for pending assignments:
- Map assignment subjects to existing study classes/categories
- Suggest studying for upcoming assignments:
  > "You have a **Spanish quiz** due tomorrow on Canvas. Want to study **pretérito** verbs to prepare?"

### Todoist → Study Scheduling

After a study session ends:
> "Would you like me to schedule your next study session in Todoist? Based on your performance, I'd suggest reviewing **[weak area]** in 2-3 days."

If yes, use `skill_view("todoist")` to create a task with appropriate duration and scheduling.

### Memory → Preferences

Save high-level study preferences to the memory tool (NOT study data — that goes in the database):
- Preferred question types per subject
- Study schedule preferences (morning/evening, session length)
- Any corrections the user makes to your behavior

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `sentence-transformers` not installed | Semantic search falls back to FTS5 text search. Install with `pip install sentence-transformers` for better deduplication. |
| Database not found | Created automatically on first use at `~/.hermes/study_data.db` |
| Class/category not found | Create with `create_class` / `create_category` before recording |
| Large file content | Use `--content -` flag and pipe content via stdin |
| Score seems wrong | Scores use a rolling window of last 20 attempts — recent performance matters more |
| FTS5 not available | Some SQLite builds don't include FTS5. Embedding search is preferred anyway. |

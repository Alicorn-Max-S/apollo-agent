# Study Question Types Reference

This document describes the 10 question types available for study sessions. Each entry covers when to use it, how to generate questions, expected answer formats, and accuracy checking rules.

---

## 1. Fill in the Blank (`fill_in_blank`)

**Best for:** Vocabulary, grammar rules, formulas, key terms in context

**How to generate:** Take a sentence from study material. Remove one key term and replace with `_____`. The removed term is the correct answer.

**Example:**
> The chemical formula for water is _____.
> *Answer: H₂O*

**Answer checking:**
- Only evaluate the blank, not surrounding text
- Case-insensitive for non-proper nouns
- Accept equivalent representations (H2O = H₂O)

---

## 2. Conjugation (`conjugation`)

**Best for:** Language verb practice (Spanish, French, German, etc.)

**How to generate:** Provide a verb in infinitive form, a subject pronoun, and a tense. Ask the user to conjugate.

**Example:**
> Conjugate **hablar** for **yo** in the **pretérito**.
> *Answer: hablé*

**Answer checking:**
- Accept with or without subject pronoun ("yo hablé" = "hablé")
- Case-insensitive
- Accent variations: mark correct but flag the missing accent ("hable" → correct concept, note accent)
- Wrong tense/form = incorrect, explain the rule and correct conjugation

---

## 3. Vocabulary (`vocabulary`)

**Best for:** Definitions, translations, terminology

**How to generate:** Present a term and ask for its definition, or present a definition and ask for the term. Can be target→native or native→target language.

**Example:**
> What does **ephemeral** mean?
> *Answer: lasting for a very short time*

**Answer checking:**
- Case-insensitive
- Accept common synonyms ("brief", "short-lived", "fleeting" all valid for ephemeral)
- Accept singular/plural variations with a note
- For translations, accept common alternative translations

---

## 4. Full Sentence (`full_sentence`)

**Best for:** History, literature analysis, science explanations, any open-ended topic

**How to generate:** Ask a question that requires a complete sentence or short paragraph response. Should target specific concepts from the study material.

**Example:**
> Explain why the Treaty of Versailles contributed to World War II.
> *Answer should mention: harsh reparations, German resentment, economic instability, rise of nationalism*

**Answer checking:**
- Check that key concepts/facts are present (keep a mental checklist)
- Don't penalize grammar or writing style differences
- Note if important details are missing but don't mark fully incorrect for partial answers
- Give credit for correct reasoning even if wording differs from source material

---

## 5. Multiple Choice (`multiple_choice`)

**Best for:** Low-knowledge areas (score 0–3), review sessions, concept recognition

**How to generate:** Write the question with 4 options (A–D). One correct, three plausible distractors. Distractors should be related but clearly wrong to someone who knows the material.

**Example:**
> What is the powerhouse of the cell?
> A) Nucleus
> B) Mitochondria
> C) Ribosome
> D) Endoplasmic reticulum
> *Answer: B*

**Answer checking:**
- Accept letter (A/B/C/D, lowercase ok) or the full text of the option
- Only one correct answer

---

## 6. True/False (`true_false`)

**Best for:** Quick concept checks, common misconceptions, fact verification

**How to generate:** Write a statement that is clearly true or false based on the study material. Avoid ambiguous statements. For false statements, make the error specific and correctable.

**Example:**
> True or False: The mitochondria is responsible for photosynthesis.
> *Answer: False — mitochondria are responsible for cellular respiration. Chloroplasts handle photosynthesis.*

**Answer checking:**
- Accept "true"/"false", "t"/"f", "yes"/"no"
- The user should explain their reasoning — evaluate the explanation quality
- If user says the right T/F but gives wrong reasoning, note the reasoning issue

---

## 7. Short Answer (`short_answer`)

**Best for:** Science concepts, social studies, focused explanations (1–3 sentences)

**How to generate:** Ask a focused question that can be answered in 1–3 sentences. More specific than full_sentence but more than one word.

**Example:**
> What is the difference between mitosis and meiosis?
> *Answer: Mitosis produces two identical daughter cells for growth/repair, while meiosis produces four genetically diverse gametes for reproduction.*

**Answer checking:**
- Check for key distinguishing facts
- Don't require exact wording
- Partial credit: note which parts were correct and which were missing
- Accept different valid explanations of the same concept

---

## 8. Matching (`matching`)

**Best for:** Vocabulary pairs, dates↔events, terms↔definitions, cause↔effect

**How to generate:** Present two columns (A and B) with 4–6 items each. Ask user to match items from column A to column B.

**Example:**
> Match the term to its definition:
> 1. Osmosis        A. Movement of molecules from high to low concentration
> 2. Diffusion      B. Movement of water across a semipermeable membrane
> 3. Active transport C. Movement requiring cellular energy
>
> *Answer: 1→B, 2→A, 3→C*

**Answer checking:**
- Accept any clear format: "1-B, 2-A, 3-C" or "1B 2A 3C" or numbered list
- Evaluate each pair individually — give partial credit
- Score = correct pairs / total pairs

---

## 9. Ordering (`ordering`)

**Best for:** Timelines, process steps, mathematical operations, historical sequences

**How to generate:** Present 4–6 items in random order. Ask user to arrange them in the correct sequence (chronological, procedural, etc.).

**Example:**
> Put these events in chronological order:
> A. Declaration of Independence signed
> B. Boston Tea Party
> C. Battle of Yorktown
> D. First Continental Congress
>
> *Answer: B, D, A, C (1773, 1774, 1776, 1781)*

**Answer checking:**
- Accept letters, numbers, or item text in sequence
- Evaluate position-by-position — give partial credit
- If adjacent items are swapped, note the error but acknowledge the rest is correct

---

## 10. Diagram Label (`diagram_label`)

**Best for:** Anatomy, geography, circuit diagrams, cell biology, any visual material

**How to generate:** Describe a diagram verbally (or reference an uploaded image). Identify specific parts and ask the user to label them. Number the parts clearly.

**Example:**
> In a plant cell diagram, label the following numbered parts:
> 1. The outer boundary of the cell
> 2. The organelle responsible for photosynthesis
> 3. The large fluid-filled structure in the center
>
> *Answers: 1. Cell wall, 2. Chloroplast, 3. Central vacuole*

**Answer checking:**
- Evaluate each label independently
- Accept common alternative names (cell wall = cell boundary)
- Case-insensitive
- Give partial credit for each correct label

---

## General Rules for All Types

1. **Always explain** why an answer is correct or incorrect
2. **For incorrect answers**, provide the correct answer AND a brief rule/explanation
3. **Accent leniency**: In language questions, accept missing accents but flag them ("Correct! Note: the accent should be on the é → hablé")
4. **Partial credit**: For types that have multiple parts (matching, ordering, diagram_label), evaluate each part and give partial credit
5. **Don't penalize** formatting differences — focus on content accuracy

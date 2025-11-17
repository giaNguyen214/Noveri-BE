decompose_prompt = """
Your task is to decompose the text into atomic claims.
The answer should be a JSON with a single key "claims", with the value of a list of strings, where each string should be a context-independent claim, representing one fact.
Note that:
1. Each claim should be concise (less than 15 words) and self-contained.
2. Avoid vague references like 'he', 'she', 'it', 'this', 'the company', 'the man' and using complete names.
3. Generate at least one claim for each single sentence in the texts.

For example,
Text: Mary is a five-year old girl, she likes playing piano and she doesn't like cookies.
Output:
{{"claims": ["Mary is a five-year old girl.", "Mary likes playing piano.", "Mary doesn't like cookies."]}}

Text: {doc}
Output:
"""

checkworthy_prompt = """
Your task is to evaluate each provided statement to determine if it presents information whose factuality can be objectively verified by humans, irrespective of the statement's current accuracy. Consider the following guidelines:
1. Opinions versus Facts: Distinguish between opinions, which are subjective and not verifiable, and statements that assert factual information, even if broad or general. Focus on whether there's a factual claim that can be investigated.
2. Clarity and Specificity: Statements must have clear and specific references to be verifiable (e.g., "he is a professor" is not verifiable without knowing who "he" is).
3. Presence of Factual Information: Consider a statement verifiable if it includes factual elements that can be checked against evidence or reliable sources, even if the overall statement might be broad or incorrect.
Your response should be in JSON format, with each statement as a key and either "Yes" or "No" as the value, along with a brief rationale for your decision.

For example, given these statements:
1. Gary Smith is a distinguished professor of economics.
2. He is a professor at MBZUAI.
3. Obama is the president of the UK.

The expected output is:
{{
    "Gary Smith is a distinguished professor of economics.": "Yes (The statement contains verifiable factual information about Gary Smith's professional title and field.)",
    "He is a professor at MBZUAI.": "No (The statement cannot be verified due to the lack of clear reference to who 'he' is.)",
    "Obama is the president of the UK.": "Yes (This statement contain verifiable information regarding the political leadership of a country.)"
}}

For these statements:
{texts}

The output should be:
"""


naver_system_prompt = """
This system is an **Advanced Critical Reasoning and Consistency Verification Engine**. Your sole function is to meticulously analyze two input texts (which may be in English or Vietnamese) to verify the factual consistency of the first against the second, which is designated as the 'source of truth'.
Your output **MUST** be a single, strictly formatted JSON object.
---

### INPUT SPECIFICATION
1.  **`NEW TEXT`**: The user-generated text/assertion that requires verification.
2.  **`RETRIEVED INFORMATION (RAG)`**: The 'source of truth' knowledge base against which the `NEW TEXT` is verified.
---

### TASK OBJECTIVES
Your mission is to perform a rigorous, sentence-by-sentence comparison of `NEW TEXT` against `RAG` to identify all factual conflicts and critical contextual omissions.
**You MUST identify every single factual conflict without omission.**

#### 1. Identify ALL Factual Conflicts (Inconsistencies)
* Scan for any statement in `NEW TEXT` that **contradicts, distorts, or is factually inconsistent** with the `RAG`.
* This includes **explicit errors** (wrong names, dates, locations, quantities) and **subtle errors** (incorrect relationships, misaligned terminology, or logical inferences **not directly supported** by the `RAG`).
* For **every** conflict, provide the following three elements:
    * **`new_text_snippet`**: The **verbatim snippet** from `NEW TEXT` containing the error (in its original language).
    * **`conflicting_rag_snippets`**: **All relevant, verbatim snippets** from `RAG` that prove the contradiction (in its original language).
    * **`reason`**: A detailed explanation of the conflict. Synthesize the information retrieved through RAG with the model’s internal knowledge to produce a clear, coherent, and comprehensive explanation. The reasoning must be well-structured, easy to understand, and fully articulate the underlying conflict.. **(MUST BE IN VIETNAMESE)**

#### 2. Identify Contextual Omissions (Suggestions)
* Evaluate if the `NEW TEXT` **omits crucial context, necessary nuance, or foundational information** present in the `RAG`. An omission is critical if its absence makes the `NEW TEXT` misleading, incomplete, or potentially misinterpretable.
* For **every** critical omission, provide the following two elements:
    * **`missing_context_description`**: A brief description of the key information that is missing. **(MUST BE IN VIETNAMESE)**
    * **`suggested_addition`**: Provide a constructive suggestion for how to incorporate the missing context. The suggestion must be grounded in the information retrieved from RAG and enhanced by the model’s reasoning capabilities, ensuring it is practical, polished, and professionally articulated.. **(MUST BE IN VIETNAMESE)**

#### 3. Provide an Overall Summary
* Write a concise summary of the overall consistency level, highlighting the most severe conflicts (if any) and concluding on the need for improvement or revision. **(MUST BE IN VIETNAMESE)**
---

### OUTPUT FORMAT (STRICTLY JSON ONLY)
You **MUST** return a single, valid JSON object, structured precisely as follows. **DO NOT** add any introductory or concluding text outside of the JSON block.

{
  "conflicts": [
    {
      "new_text_snippet": "<verbatim quote from NEW TEXT (Original Language)>",
      "conflicting_rag_snippets": [
        "<verbatim quote from RAG (Original Language)>",
        "... other necessary RAG quotes ..."
      ],
      "reason": "<A well-articulated explanation of the conflict, based on RAG and AI knowledge. MUST BE IN VIETNAMESE.>"
    }
  ],
  "suggestions": [
    {
      "missing_context_description": "<A brief description of the missing context. MUST BE IN VIETNAMESE.>",
      "suggested_addition": "<A well-articulated suggestion for improvement, based on RAG and AI knowledge. MUST BE IN VIETNAMESE.>"
    }
  ],
  "summary": "<An overall summary of consistency and key issues. MUST BE IN VIETNAMESE.>"
}

"""
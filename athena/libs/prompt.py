from athena.core.models import MessagePrompt, ChatHistory


class GPTPrompt:
    def __new__(cls, history: str, question: str) -> str:
        query_prompt_template: str = """
        Below is a history of the conversation so far, and a new question asked by the user that needs to be answered by searching in a knowledge base about a companies internal documents.
        Generate a search query based on the conversation and the new question. 
        Do not include cited source filenames and document names e.g info.txt or doc.pdf in the search query terms.
        Do not include any text inside [] or <<>> in the search query terms.
        If the question is not in English, translate the question to English before generating the search query.

        Chat History:
        {chat_history}

        Question:
        {question}

        Search query:
        """
        return query_prompt_template.format(chat_history=history, question=question)


class FollowUpQuestionsPrompt:
    def __new__(cls) -> str:
        prompt = """
            Generate three very brief follow-up questions that the user would likely ask next about their companies internal document. 
            Use double angle brackets to reference the questions, e.g. <<Are there exclusions for aws tags?>>.
            Try not to repeat questions that have already been asked.
            Only generate questions and do not generate any text before or after the questions, such as 'Next Questions'
        """
        return prompt


class ChatGPTPrompt:
    def __new__(
        cls, sources: str, history: list[ChatHistory], followup_questions: str
    ) -> list[dict]:
        system_prompt_content = f"""
            Assistant helps the company employees with questions regarding company documents. Be brief in your answers.
            Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. Do not generate answers that don't use the sources below. If asking a clarifying question to the user would help, ask the question.
            For tabular information return it as an html table. Do not return markdown format.
            Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response. Use square brakets to reference the source, e.g. [info1.txt]. Don't combine sources, list each source separately, e.g. [info1.txt][info2.pdf].
            {followup_questions}
            Sources:
            {sources}
        """
        system_prompt = MessagePrompt(
            role="system", content=system_prompt_content, name="system"
        ).dict()
        assistant_prompt = MessagePrompt(
            role="assistant", content="Remember your name is Athena", name="athena"
        ).dict()
        final_prompt = [system_prompt, assistant_prompt]
        for hist in history:
            final_prompt.append(
                MessagePrompt(role="user", content=hist.user, name="employee").dict()
            )
            final_prompt.append(
                MessagePrompt(
                    role="assistant",
                    content=hist.bot if hist.bot is not None else "",
                    name="athena",
                ).dict()
            )

        return final_prompt

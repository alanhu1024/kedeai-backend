import agenta as ag
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

default_prompt = """
**撰写一封电子邮件**，发件人为 {from_sender}，收件人为 {to_receiver}，采用指定的语气和风格：{email_style}。电子邮件的主要内容如下：{email_content}。

请使用以下格式：
主题： <主题>

<正文>

**流程**：

**(1) 确定电子邮件的主要要点：**
1. 确定所提供内容的中心主题。
2. 提取次要信息或支持性观点。

**(2) 根据给定的语气和风格 {{ style }}，为每个要点构建句子：**
3. 创建一个引人入胜的开头句，用于设定语气和介绍主题。
4. 构思句子，为之前确定的每个要点增添深度或背景信息。

**(3) 起草电子邮件的初步版本：**
使用前一步骤中构建的句子来撰写一封连贯而引人入胜的电子邮件。确保流畅自然，并且每个句子之间过渡顺畅。

**(4) 分析电子邮件，并列出改进的方法：**
5. 确定信息可能不清晰或需要补充信息的地方。
6. 考虑语言或语气可能需要增强以更具说服力或感情表达的地方。
7. 评估电子邮件是否符合风格要求，如有不符，识别出偏差。

**(5) 根据所得的见解重新撰写电子邮件：**
重新修改初稿，纳入前一步骤中确定的改进内容。力求以最有效的方式呈现信息，同时严格遵循规定的语气和风格。

"""


@ag.post
def generate(
        from_sender: str,
        to_receiver: str,
        email_style: str,
        email_content: str,
        temperature: ag.FloatParam = 0.9,
        prompt_template: ag.TextParam = default_prompt,
) -> str:
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=temperature, openai_proxy="http://192.168.153.1:3389")
    prompt = PromptTemplate(
        input_variables=["from_sender", "to_receiver", "email_style", "email_content"],
        template=prompt_template,
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    output = chain.run(
        from_sender=from_sender,
        to_receiver=to_receiver,
        email_style=email_style,
        email_content=email_content,
    )

    return output

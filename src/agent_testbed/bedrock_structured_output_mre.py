from langchain_aws import ChatBedrock, ChatBedrockConverse
from langchain_aws.chat_models.bedrock import convert_messages_to_prompt_mistral
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


from typing import TypedDict
from pydantic import BaseModel


bedrock_mistral_model = ChatBedrock(model_id="mistral.mistral-7b-instruct-v0:2")

openai_model = ChatOpenAI(model="gpt-4o-mini")

prompt = [
    SystemMessage(
        "you are a helpful assistant knowledgeale aboug geography. output json structure with key 'response_text'"
    ),
    HumanMessage("what is capital of the state of hawaii? only return the city's name.  output city name."),
]


def call_with_structured_output(this_model, this_prompt):
    import json

    class TestReturn(TypedDict):
        response_text: str

    interface_name = this_model.__class__.__name__
    model_id = this_model.model_id if hasattr(this_model, "model_id") else this_model.model_name

    if model_id.startswith("mistral"):
        prompt = convert_messages_to_prompt_mistral(this_prompt)
    else:
        prompt = this_prompt

    structured_call = this_model.with_structured_output(TestReturn)
    response = structured_call.invoke(prompt)

    print(f"\n\n{interface_name} for {model_id} WITH structured output:\n{response}")


def call_no_sturcutured_output(this_model, this_prompt):

    interface_name = this_model.__class__.__name__
    model_id = this_model.model_id if hasattr(this_model, "model_id") else this_model.model_name

    if model_id.startswith("mistral"):
        prompt = convert_messages_to_prompt_mistral(this_prompt)
    else:
        prompt = this_prompt

    response = this_model.invoke(prompt)
    print(f"\n\n{interface_name} for {model_id} NO structured output {type(response)}:\n{response}")


call_with_structured_output(bedrock_mistral_model, prompt)
call_no_sturcutured_output(bedrock_mistral_model, prompt)

call_with_structured_output(openai_model, prompt)
call_no_sturcutured_output(openai_model, prompt)

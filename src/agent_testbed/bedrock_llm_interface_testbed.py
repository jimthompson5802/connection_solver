from src.agent.bedrock_anthropic_tools import LLMBedrockHaikuInterface
import boto3

llm_interface = LLMBedrockHaikuInterface()

client = boto3.client("bedrock")

print("all done")

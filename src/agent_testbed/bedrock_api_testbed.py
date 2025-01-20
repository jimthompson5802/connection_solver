import boto3
import pprint as pp

pp = pp.PrettyPrinter(indent=4)


client = boto3.client("bedrock")

pp.pprint(client.get_foundation_model(modelIdentifier="mistral.mistral-7b-instruct-v0:2"))

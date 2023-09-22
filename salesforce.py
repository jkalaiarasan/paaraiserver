from simple_salesforce import Salesforce as SimpleSalesforce
import os

class Salesforce:
    def __init__(self):
        try:
            self.username = os.environ['SALESFORCE_USERNAME']
            self.password = os.environ['SALESFORCE_PASSWORD']
            self.security_token = os.environ['SALESFORCE_SECURITY_TOKEN']
            self.sf = SimpleSalesforce(username=self.username, password=self.password, security_token=self.security_token)
        except KeyError as e:
            print(f"Error: Environment variable {e.args[0]} is not set. Please set all required environment variables before running the application.")
            # You can choose to raise an exception, exit the application, or take other appropriate actions here.

    def query(self, query):
        try:
            result = self.sf.query_all(query)
            return result
        except Exception as e:
            print(f"Salesforce query failed: {e}")

if __name__ == "__main__":
    sf = Salesforce()

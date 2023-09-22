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

    def query(self, query):
        try:
            result = self.sf.query_all(query)
            return result
        except Exception as e:
            print(f"Salesforce query failed: {e}")
            
    def create(self, sobject, data):
        print(sobject)
        try:
            if not self.sf.session_id:
                self.sf.login(self.username, self.password + self.security_token)
            sf_object = self.sf.__getattr__(sobject)
            response = sf_object.create(data)
            return response
        except Exception as e:
            print(f"Salesforce create failed: {e}")

if __name__ == "__main__":
    sf = Salesforce()

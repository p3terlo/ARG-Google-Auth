First, set up virtual env and activate
Then, pip install -r requirements.txt


User Creation:
-Expect users to primarily log in to your website using an OAuth connection (to get API key AKA channel partners)
- When a user logs in using an OAuth connection (Github, Google, Facebook, etc.), an account is automatically created for them on our website in the process

Helpful read to understand the process and concepts behind Flask-Dance:
https://flask-dance.readthedocs.io/en/latest/understanding-the-magic.html
https://flask-dance.readthedocs.io/en/v3.0.0/multi-user.html
https://stackoverflow.com/questions/47643448/flask-dance-cannot-get-oauth-token-without-an-associated-user/48718671#48718671

Example code:
https://github.com/singingwolfboy/flask-dance-google-sqla
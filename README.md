# sms-fortune-cookie
a playful project for exchanging fortunes w/ strangers

## About
This is a flask app that handles text message exchanges with strangers. It uses [Twilio](https://www.twilio.com/) to send/receive SMS.

In a nutshell, the app:
- texts a prompt (currently the topic is crowdsourced fortune cookie fortunes, but this can be adapted to fit other topics)
- stores responses
- texts randomly selected responses from strangers
- texts notifications when responses have been seen
- allows admins to moderate responses

#### Try it out: 1 (530) 212-6073

## Setup

**1. Make sure you have OS level dependencies**
- Python 3
- MySQL

**2. Clone this repo**
```bash
git clone https://github.com/buzzfeed-openlab/sms-fortune-cookie.git
cd sms-fortune-cookie
```

**3. Install required python libraries**

(Optional but recommended: do this within a python virtual environment)

Install requirements:
```bash
pip install -r requirements.txt
```

**4. create a MySQL database**

```bash
mysql -u root
```
& then
```bash
create database sms_fortune_cookie;
```

*If you're working locally, you're good to go. But if you're going to host this on a shared server you probably want to create a new user for this database instead of using `root`.*

**5. Configure the app**

There are two ways to do this: (a) making a config file or (b) setting environment variables.

You will need the credentials from your Twilio account & number to configure the app. You can find your Twilio keys on https://www.twilio.com/console

**Option A**  
Copy the example secret config file
```bash
cp sms_swap/config_vars_secret.py.example sms_swap/config_vars_secret.py
```

Then, edit `sms_swap/config_vars_secret.py`.

**Option B**  
see `sms_swap/config_vars_secret.py.example` for the names of environment variables to set & descriptions of what the values should look like.

**6. Run the app locally**
```bash
python application.py
```

**7. Initialize the database**

  Visit the `/initialize` route (e.g. `localhost:5000/intialize`) & enter admin credentials (`ADMIN_USER` & `ADMIN_PASS`). This will create the table for storing responses.


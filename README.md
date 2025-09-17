You need to have a google email app password first, then set the env by export GMAIL_APP_PASSWORD="xxx"
Then update the sender email in the code to be your own email
You can update the site ids, the time range, and excluded date to get the results you want. For now it will only search for Fri and Sat nights.
Then run the script in a loop
  while true; do
    python3 v3.py
  done   

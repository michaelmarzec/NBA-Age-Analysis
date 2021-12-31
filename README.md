# NBA-Age-Analysis
 Analysis of NBA in-season age trends

## Architecture
 
### AWS Lambda (Daily Scraping)
 - /utils/lambda_function.py used as AWS Lambda script

 <ins>layered ARNs</ins>
  - arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-numpy:23
  - arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-pandas:45
  - arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-beautifulsoup4:13
  - arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-lxml:9

### Zappa (Serverless Hosting)
  - /flask/flask-main.py uploaded as flask app using zappa library
  - html files located within /flask/templtes/

  <ins>website link</ins> 
    - https://15xu0h4j6i.execute-api.us-east-2.amazonaws.com/dev


### Local Processing
 /utils/local_main.py

 - accesses and updates local file ./age_tracking.csv
 
 
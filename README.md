# NBA-Age-Analysis
 Analysis of NBA in-season age trends

## Architecture
 
### AWS Lambda
 /utils/lambda_function.py used as AWS Lambda script

 layered ARNs
  - arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-numpy:23
  - arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-pandas:45
  - arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-beautifulsoup4:13
  - arn:aws:lambda:us-east-2:770693421928:layer:Klayers-python38-lxml:9

### Local Processing
 /utils/local_main.py

 - accesses and updates local file ./age_tracking.csv
 
 
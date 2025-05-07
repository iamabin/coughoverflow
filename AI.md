# AI Usage

I used ChatGPT to help me to provide the debug insight.

- endpoint /analysis post   
  **Prompt**:"Here is the error(cpoied from the pytest) please tell me how to fix it."  
   **Response** : You should make sure you can get output from overflowengine.
    print("🧠 STDOUT:", repr(result.stdout))
      print("❌ STDERR:", repr(result.stderr))
      print("📦 RETURN CODE:", result.returncode)
- Generate the base project template for SQS integration, mostly worker.py and debug credentials issue.
    
  **Prompt:** "I am using flask api and deploy to AWS please write me a template of using sqs to achieve asyc."  
  **Response(excerpt)**:
    ```bash
    
    sqs_client = boto3.client(
        "sqs",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    def handle_message(message_body):
        print(f"Processing: {message_body}")
        # Simulate long-running task
        time.sleep(2)
        print("Done")
    
    def poll_queue():
        while True:
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )
    
            messages = response.get('Messages', [])
            for msg in messages:
                body = msg['Body']
                handle_message(body)
    
                # Delete message after processing
                sqs_client.delete_message(
                    QueueUrl=SQS_QUEUE_URL,
                    ReceiptHandle=msg['ReceiptHandle']
                )
    
    
    ```
    
  **Prompt:** "botocore.exceptions.NoCredentialsError: Unable to locate credentials Why?"

  **Response(excerpt):**
    The error botocore.exceptions.NoCredentialsError: Unable to locate credentials means your Python application cannot find AWS credentials to authenticate with AWS services (like SQS).

      1. Set environment variables (recommended for local/dev)
        
        
        ```
        export AWS_ACCESS_KEY_ID=your_access_key
        export AWS_SECRET_ACCESS_KEY=your_secret_key
        You can also add them to a .env file and load them using python-dotenv.
        ```
        
        ✅ 2. Use AWS credentials file.....






I used the provided code to test the overflowengine and founded that it is not working properly. After that I rewritten the code to make it work 

    



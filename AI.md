# AI Usage

I used ChatGPT to help me to provide the debug insight.

- endpoint /analysis post   
  "Here is the error(cpoyed from the pytest) please tell me how to fix it."  
   The response is: You should make sure you can get output from overflowengine.
    print("🧠 STDOUT:", repr(result.stdout))
      print("❌ STDERR:", repr(result.stderr))
      print("📦 RETURN CODE:", result.returncode)
  
I used the provided code to test the overflowengine and founded that it is not working properly. After that I rewritten the code to make it work 

    


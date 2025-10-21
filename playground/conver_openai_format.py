import json

input_file = "C:\\Users\\hayka\\Desktop\\New folder (3)\\nmap\\dataset_20251020_202206.jsonl"         
output_file = "C:\\Users\\hayka\\Desktop\\New folder (3)\\nmap\\data_converted.jsonl"   

with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
    for line in infile:
        line = line.strip()
        if not line:
            continue  
        try:
            item = json.loads(line)
            
            formatted = {
                "messages": [
                    {"role": "user", "content": item["input"]},
                    {"role": "assistant", "content": item["output"]}
                ]
            }
            json.dump(formatted, outfile, ensure_ascii=False)
            outfile.write("\n")
        except Exception as e:
            print(f"Hata oluştu: {e}\nSatır: {line}")
